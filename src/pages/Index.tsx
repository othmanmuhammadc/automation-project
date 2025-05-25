
import React, { useState } from 'react';
import { AutomationDashboard } from '@/components/AutomationDashboard';
import { ConfigManager } from '@/components/ConfigManager';
import { ScriptGenerator } from '@/components/ScriptGenerator';
import { VideoCreator } from '@/components/VideoCreator';
import { UploadManager } from '@/components/UploadManager';
import { LogViewer } from '@/components/LogViewer';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Settings, FileText, Video, Upload, Activity } from 'lucide-react';

const Index = () => {
  const [activeWorkflow, setActiveWorkflow] = useState<string>('full_auto');
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${timestamp}] ${message}`]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 text-center">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
            AI Automation Tool
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Intelligent automation for content creation, video generation, and YouTube uploads
          </p>
        </div>

        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="grid w-full grid-cols-6 mb-8 bg-slate-800 border-slate-700">
            <TabsTrigger value="dashboard" className="text-slate-300 data-[state=active]:text-white">
              <Activity className="w-4 h-4 mr-2" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="config" className="text-slate-300 data-[state=active]:text-white">
              <Settings className="w-4 h-4 mr-2" />
              Config
            </TabsTrigger>
            <TabsTrigger value="script" className="text-slate-300 data-[state=active]:text-white">
              <FileText className="w-4 h-4 mr-2" />
              Script
            </TabsTrigger>
            <TabsTrigger value="video" className="text-slate-300 data-[state=active]:text-white">
              <Video className="w-4 h-4 mr-2" />
              Video
            </TabsTrigger>
            <TabsTrigger value="upload" className="text-slate-300 data-[state=active]:text-white">
              <Upload className="w-4 h-4 mr-2" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="logs" className="text-slate-300 data-[state=active]:text-white">
              <FileText className="w-4 h-4 mr-2" />
              Logs
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <AutomationDashboard 
              activeWorkflow={activeWorkflow}
              setActiveWorkflow={setActiveWorkflow}
              onLog={addLog}
            />
          </TabsContent>

          <TabsContent value="config">
            <ConfigManager onLog={addLog} />
          </TabsContent>

          <TabsContent value="script">
            <ScriptGenerator onLog={addLog} />
          </TabsContent>

          <TabsContent value="video">
            <VideoCreator onLog={addLog} />
          </TabsContent>

          <TabsContent value="upload">
            <UploadManager onLog={addLog} />
          </TabsContent>

          <TabsContent value="logs">
            <LogViewer logs={logs} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
