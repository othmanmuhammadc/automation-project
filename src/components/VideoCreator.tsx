
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Video, Play, Download, Upload } from 'lucide-react';
import { toast } from 'sonner';

interface VideoCreatorProps {
  onLog: (message: string) => void;
}

export const VideoCreator: React.FC<VideoCreatorProps> = ({ onLog }) => {
  const [scriptFile, setScriptFile] = useState<File | null>(null);
  const [videoSettings, setVideoSettings] = useState({
    voice: 'elfy',
    style: 'anime',
    aspectRatio: '9:16',
    quality: '1080p',
    fps: 60,
    duration: 60
  });
  const [isCreating, setIsCreating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [createdVideo, setCreatedVideo] = useState<string | null>(null);

  const creationSteps = [
    'Analyzing script content',
    'Generating voiceover',
    'Creating visual elements',
    'Applying anime style',
    'Synchronizing audio and video',
    'Rendering final video',
    'Optimizing for platform'
  ];

  const handleScriptUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setScriptFile(file);
      onLog(`Script file uploaded: ${file.name}`);
      toast.success('Script file uploaded successfully!');
    }
  };

  const handleCreateVideo = async () => {
    if (!scriptFile) {
      toast.error('Please upload a script file first');
      return;
    }

    setIsCreating(true);
    setProgress(0);
    onLog('Starting video creation process...');

    for (let i = 0; i < creationSteps.length; i++) {
      setCurrentStep(creationSteps[i]);
      onLog(`Step ${i + 1}: ${creationSteps[i]}`);
      
      // Simulate step execution with varying durations
      const stepDuration = Math.random() * 2000 + 1000;
      await new Promise(resolve => setTimeout(resolve, stepDuration));
      
      const stepProgress = ((i + 1) / creationSteps.length) * 100;
      setProgress(stepProgress);
    }

    // Simulate video creation completion
    const videoId = `video_${Date.now()}`;
    setCreatedVideo(videoId);
    setIsCreating(false);
    setCurrentStep('Completed');
    
    onLog('Video creation completed successfully');
    toast.success('Video created successfully!');
  };

  const handlePreview = () => {
    onLog('Opening video preview...');
    toast.info('Video preview would open in CapCut');
  };

  const handleDownload = () => {
    onLog('Downloading video...');
    toast.success('Video download started');
  };

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Video Creation</CardTitle>
          <CardDescription className="text-slate-400">
            Create videos using CapCut AI with your script
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="text-slate-300">Script File</Label>
            <Input
              type="file"
              accept=".txt,.json,.md"
              onChange={handleScriptUpload}
              className="bg-slate-700 border-slate-600 text-white file:bg-slate-600 file:text-white file:border-0"
            />
            {scriptFile && (
              <p className="text-sm text-green-400 mt-1">
                ✓ {scriptFile.name} uploaded
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">Voice</Label>
              <Select 
                value={videoSettings.voice} 
                onValueChange={(value) => setVideoSettings(prev => ({ ...prev, voice: value }))}
              >
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="elfy" className="text-white">Elfy</SelectItem>
                  <SelectItem value="narrator" className="text-white">Narrator</SelectItem>
                  <SelectItem value="energetic" className="text-white">Energetic</SelectItem>
                  <SelectItem value="calm" className="text-white">Calm</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-slate-300">Style</Label>
              <Select 
                value={videoSettings.style} 
                onValueChange={(value) => setVideoSettings(prev => ({ ...prev, style: value }))}
              >
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="anime" className="text-white">Anime</SelectItem>
                  <SelectItem value="realistic" className="text-white">Realistic</SelectItem>
                  <SelectItem value="cartoon" className="text-white">Cartoon</SelectItem>
                  <SelectItem value="minimalist" className="text-white">Minimalist</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label className="text-slate-300">Aspect Ratio</Label>
              <Select 
                value={videoSettings.aspectRatio} 
                onValueChange={(value) => setVideoSettings(prev => ({ ...prev, aspectRatio: value }))}
              >
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="9:16" className="text-white">9:16 (Vertical)</SelectItem>
                  <SelectItem value="16:9" className="text-white">16:9 (Horizontal)</SelectItem>
                  <SelectItem value="1:1" className="text-white">1:1 (Square)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-slate-300">Quality</Label>
              <Select 
                value={videoSettings.quality} 
                onValueChange={(value) => setVideoSettings(prev => ({ ...prev, quality: value }))}
              >
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="1080p" className="text-white">1080p</SelectItem>
                  <SelectItem value="720p" className="text-white">720p</SelectItem>
                  <SelectItem value="4k" className="text-white">4K</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-slate-300">FPS</Label>
              <Select 
                value={videoSettings.fps.toString()} 
                onValueChange={(value) => setVideoSettings(prev => ({ ...prev, fps: parseInt(value) }))}
              >
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="30" className="text-white">30 FPS</SelectItem>
                  <SelectItem value="60" className="text-white">60 FPS</SelectItem>
                  <SelectItem value="120" className="text-white">120 FPS</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label className="text-slate-300">Duration (seconds)</Label>
            <Input
              type="number"
              value={videoSettings.duration}
              onChange={(e) => setVideoSettings(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
              className="bg-slate-700 border-slate-600 text-white"
            />
          </div>

          <Button 
            onClick={handleCreateVideo}
            disabled={!scriptFile || isCreating}
            className="w-full bg-red-600 hover:bg-red-700"
          >
            <Video className="w-4 h-4 mr-2" />
            {isCreating ? 'Creating Video...' : 'Create Video'}
          </Button>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Creation Progress</CardTitle>
          <CardDescription className="text-slate-400">
            Track your video creation progress
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {isCreating || createdVideo ? (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-slate-300">Progress</span>
                  <span className="text-slate-300">{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} className="w-full" />
              </div>

              <div className="space-y-2">
                <h4 className="text-white font-medium">Creation Steps:</h4>
                {creationSteps.map((step, index) => {
                  const stepProgress = (index + 1) / creationSteps.length * 100;
                  const isCompleted = progress >= stepProgress;
                  const isCurrent = currentStep === step;
                  
                  return (
                    <div key={index} className="flex items-center justify-between">
                      <span className={`text-sm ${
                        isCompleted ? 'text-green-400' : 
                        isCurrent ? 'text-blue-400' : 'text-slate-500'
                      }`}>
                        {index + 1}. {step}
                      </span>
                      <Badge variant={
                        isCompleted ? "default" : 
                        isCurrent ? "secondary" : "outline"
                      }>
                        {isCompleted ? '✓' : isCurrent ? '...' : '○'}
                      </Badge>
                    </div>
                  );
                })}
              </div>

              {createdVideo && (
                <div className="mt-6 p-4 bg-slate-700 rounded-lg">
                  <h4 className="text-white font-medium mb-3">Video Created Successfully!</h4>
                  <div className="space-y-2 text-sm text-slate-300">
                    <p>Video ID: {createdVideo}</p>
                    <p>Duration: {videoSettings.duration}s</p>
                    <p>Quality: {videoSettings.quality} @ {videoSettings.fps}fps</p>
                    <p>Style: {videoSettings.style}</p>
                    <p>Voice: {videoSettings.voice}</p>
                  </div>
                  
                  <div className="flex gap-2 mt-4">
                    <Button size="sm" onClick={handlePreview} className="bg-blue-600 hover:bg-blue-700">
                      <Play className="w-4 h-4 mr-2" />
                      Preview
                    </Button>
                    <Button size="sm" onClick={handleDownload} variant="outline" className="border-slate-600 text-slate-300">
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">
              <Video className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Upload a script and click "Create Video" to start</p>
              <p className="text-sm">Your video creation progress will appear here</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
