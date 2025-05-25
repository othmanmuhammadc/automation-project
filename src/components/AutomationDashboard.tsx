
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Play, Pause, Square, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';

interface AutomationDashboardProps {
  activeWorkflow: string;
  setActiveWorkflow: (workflow: string) => void;
  onLog: (message: string) => void;
}

export const AutomationDashboard: React.FC<AutomationDashboardProps> = ({
  activeWorkflow,
  setActiveWorkflow,
  onLog
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [videosCreated, setVideosCreated] = useState(0);
  const [videosUploaded, setVideosUploaded] = useState(0);

  const workflowModes = [
    { value: 'full_auto', label: 'Full Auto (Script → Video → Upload)' },
    { value: 'script_only', label: 'Script Only' },
    { value: 'video_only', label: 'Video Only' },
    { value: 'upload_only', label: 'Upload Only' },
    { value: 'script_and_video', label: 'Script + Video' },
    { value: 'video_and_upload', label: 'Video + Upload' }
  ];

  const handleStart = async () => {
    setIsRunning(true);
    setProgress(0);
    onLog(`Starting ${activeWorkflow} workflow`);
    
    const steps = getWorkflowSteps(activeWorkflow);
    
    for (let i = 0; i < steps.length; i++) {
      setCurrentStep(steps[i]);
      onLog(`Executing step: ${steps[i]}`);
      
      // Simulate step execution
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const stepProgress = ((i + 1) / steps.length) * 100;
      setProgress(stepProgress);
      
      if (steps[i].includes('Script')) {
        onLog('Script generation completed');
      } else if (steps[i].includes('Video')) {
        setVideosCreated(prev => prev + 1);
        onLog('Video creation completed');
      } else if (steps[i].includes('Upload')) {
        setVideosUploaded(prev => prev + 1);
        onLog('Video upload completed');
      }
    }
    
    setIsRunning(false);
    setCurrentStep('Completed');
    toast.success(`${activeWorkflow} workflow completed successfully!`);
  };

  const getWorkflowSteps = (workflow: string): string[] => {
    switch (workflow) {
      case 'full_auto':
        return ['Generate Script', 'Create Video', 'Upload to YouTube'];
      case 'script_only':
        return ['Generate Script'];
      case 'video_only':
        return ['Create Video'];
      case 'upload_only':
        return ['Upload to YouTube'];
      case 'script_and_video':
        return ['Generate Script', 'Create Video'];
      case 'video_and_upload':
        return ['Create Video', 'Upload to YouTube'];
      default:
        return [];
    }
  };

  const handlePause = () => {
    setIsRunning(false);
    onLog('Workflow paused');
    toast.info('Workflow paused');
  };

  const handleStop = () => {
    setIsRunning(false);
    setProgress(0);
    setCurrentStep('');
    onLog('Workflow stopped');
    toast.error('Workflow stopped');
  };

  const handleReset = () => {
    setProgress(0);
    setCurrentStep('');
    setVideosCreated(0);
    setVideosUploaded(0);
    onLog('Dashboard reset');
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card className="bg-slate-800 border-slate-700 col-span-full">
        <CardHeader>
          <CardTitle className="text-white">Workflow Control</CardTitle>
          <CardDescription className="text-slate-400">
            Configure and execute your automation workflow
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-300 mb-2 block">
              Workflow Mode
            </label>
            <Select value={activeWorkflow} onValueChange={setActiveWorkflow}>
              <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-700 border-slate-600">
                {workflowModes.map((mode) => (
                  <SelectItem key={mode.value} value={mode.value} className="text-white">
                    {mode.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2">
            <Button 
              onClick={handleStart} 
              disabled={isRunning}
              className="bg-green-600 hover:bg-green-700"
            >
              <Play className="w-4 h-4 mr-2" />
              Start
            </Button>
            <Button 
              onClick={handlePause} 
              disabled={!isRunning}
              variant="outline"
              className="border-slate-600 text-slate-300"
            >
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </Button>
            <Button 
              onClick={handleStop} 
              disabled={!isRunning}
              variant="destructive"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
            <Button 
              onClick={handleReset} 
              variant="outline"
              className="border-slate-600 text-slate-300"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Progress value={progress} className="w-full" />
            <div className="text-sm text-slate-400">
              {currentStep || 'Ready to start'}
            </div>
            <Badge variant={isRunning ? "default" : "secondary"}>
              {isRunning ? 'Running' : 'Idle'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-slate-400">Videos Created:</span>
              <span className="text-white font-semibold">{videosCreated}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Videos Uploaded:</span>
              <span className="text-white font-semibold">{videosUploaded}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Success Rate:</span>
              <span className="text-green-400 font-semibold">
                {videosCreated > 0 ? Math.round((videosUploaded / videosCreated) * 100) : 0}%
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Configuration Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">AI Model:</span>
              <Badge variant="outline">ChatGPT</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Video Quality:</span>
              <Badge variant="outline">1080p 60fps</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Channel:</span>
              <Badge variant="outline">MyAwesomeChannel</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Timezone:</span>
              <Badge variant="outline">Asia/Cairo</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
