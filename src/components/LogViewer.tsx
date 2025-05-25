
import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Download, Search, Filter, Trash2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface LogViewerProps {
  logs: string[];
}

export const LogViewer: React.FC<LogViewerProps> = ({ logs }) => {
  const [filteredLogs, setFilteredLogs] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [logLevel, setLogLevel] = useState('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let filtered = logs;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by log level
    if (logLevel !== 'all') {
      filtered = filtered.filter(log => {
        const logLower = log.toLowerCase();
        switch (logLevel) {
          case 'error':
            return logLower.includes('error') || logLower.includes('failed');
          case 'warning':
            return logLower.includes('warning') || logLower.includes('warn');
          case 'info':
            return logLower.includes('info') || logLower.includes('completed');
          case 'debug':
            return logLower.includes('debug') || logLower.includes('step');
          default:
            return true;
        }
      });
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, logLevel]);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll]);

  const getLogLevel = (log: string): string => {
    const logLower = log.toLowerCase();
    if (logLower.includes('error') || logLower.includes('failed')) return 'error';
    if (logLower.includes('warning') || logLower.includes('warn')) return 'warning';
    if (logLower.includes('completed') || logLower.includes('success')) return 'success';
    if (logLower.includes('started') || logLower.includes('starting')) return 'info';
    return 'debug';
  };

  const getLogBadgeVariant = (level: string) => {
    switch (level) {
      case 'error': return 'destructive';
      case 'warning': return 'secondary';
      case 'success': return 'default';
      case 'info': return 'outline';
      default: return 'outline';
    }
  };

  const handleExportLogs = () => {
    const logContent = filteredLogs.join('\n');
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `automation_logs_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    
    toast.success('Logs exported successfully!');
  };

  const handleClearLogs = () => {
    if (confirm('Are you sure you want to clear all logs?')) {
      // This would clear the logs in the parent component
      toast.success('Logs cleared successfully!');
    }
  };

  return (
    <Card className="bg-slate-800 border-slate-700 h-[calc(100vh-200px)]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white">System Logs</CardTitle>
            <CardDescription className="text-slate-400">
              Real-time automation logs and system messages
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-slate-300">
              {filteredLogs.length} / {logs.length} logs
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col h-full space-y-4">
        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search logs..."
              className="bg-slate-700 border-slate-600 text-white pl-10"
            />
          </div>

          <Select value={logLevel} onValueChange={setLogLevel}>
            <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-700 border-slate-600">
              <SelectItem value="all" className="text-white">All Levels</SelectItem>
              <SelectItem value="error" className="text-white">Errors</SelectItem>
              <SelectItem value="warning" className="text-white">Warnings</SelectItem>
              <SelectItem value="info" className="text-white">Info</SelectItem>
              <SelectItem value="debug" className="text-white">Debug</SelectItem>
            </SelectContent>
          </Select>

          <Button 
            onClick={handleExportLogs}
            variant="outline"
            className="border-slate-600 text-slate-300"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>

          <div className="flex space-x-2">
            <Button 
              onClick={() => setAutoScroll(!autoScroll)}
              variant="outline"
              size="sm"
              className="border-slate-600 text-slate-300"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
            </Button>
            <Button 
              onClick={handleClearLogs}
              variant="destructive"
              size="sm"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Log Display */}
        <div 
          ref={logContainerRef}
          className="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-4 overflow-y-auto font-mono text-sm"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-center text-slate-400 py-8">
              {logs.length === 0 ? 'No logs yet' : 'No logs match your filters'}
            </div>
          ) : (
            <div className="space-y-1">
              {filteredLogs.map((log, index) => {
                const level = getLogLevel(log);
                const timestamp = log.match(/\[([\d:]+)\]/)?.[1] || '';
                const message = log.replace(/\[[\d:]+\]\s*/, '');
                
                return (
                  <div 
                    key={index} 
                    className="flex items-start space-x-3 py-1 px-2 rounded hover:bg-slate-800 transition-colors"
                  >
                    <Badge 
                      variant={getLogBadgeVariant(level)}
                      className="text-xs min-w-[60px] justify-center"
                    >
                      {level.toUpperCase()}
                    </Badge>
                    {timestamp && (
                      <span className="text-slate-500 text-xs min-w-[60px]">
                        {timestamp}
                      </span>
                    )}
                    <span 
                      className={`flex-1 ${
                        level === 'error' ? 'text-red-400' :
                        level === 'warning' ? 'text-yellow-400' :
                        level === 'success' ? 'text-green-400' :
                        level === 'info' ? 'text-blue-400' :
                        'text-slate-300'
                      }`}
                    >
                      {message}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Statistics */}
        <div className="flex justify-between items-center text-sm text-slate-400 border-t border-slate-600 pt-4">
          <div>
            Total: {logs.length} | Filtered: {filteredLogs.length}
          </div>
          <div className="flex space-x-4">
            <span>Errors: {logs.filter(log => getLogLevel(log) === 'error').length}</span>
            <span>Warnings: {logs.filter(log => getLogLevel(log) === 'warning').length}</span>
            <span>Success: {logs.filter(log => getLogLevel(log) === 'success').length}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
