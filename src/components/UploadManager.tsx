
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Upload, Calendar, Clock, Tag, Captions } from 'lucide-react';
import { toast } from 'sonner';

interface UploadManagerProps {
  onLog: (message: string) => void;
}

interface UploadedVideo {
  id: string;
  title: string;
  uploadedAt: string;
  status: 'uploaded' | 'scheduled' | 'processing';
  scheduledFor?: string;
}

export const UploadManager: React.FC<UploadManagerProps> = ({ onLog }) => {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [uploadDetails, setUploadDetails] = useState({
    title: '',
    description: '',
    tags: '',
    visibility: 'public',
    category: 'Entertainment',
    thumbnail: null as File | null
  });
  const [scheduleSettings, setScheduleSettings] = useState({
    scheduleVideo: true,
    timeSlot: '06:00',
    timezone: 'Asia/Cairo',
    autoTags: true,
    autoCaptions: true
  });
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedVideos, setUploadedVideos] = useState<UploadedVideo[]>([
    {
      id: 'vid_001',
      title: 'AI Productivity Tips',
      uploadedAt: '2024-01-15 14:30',
      status: 'uploaded'
    },
    {
      id: 'vid_002',
      title: 'Future of Technology',
      uploadedAt: '2024-01-14 09:15',
      status: 'scheduled',
      scheduledFor: '2024-01-16 12:00'
    }
  ]);

  const timeSlots = ['06:00', '12:00', '18:00', '00:00'];
  const categories = [
    'Entertainment', 'Education', 'Technology', 'Gaming', 'Music',
    'Sports', 'News', 'Comedy', 'Science', 'Travel'
  ];

  const handleVideoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setVideoFile(file);
      onLog(`Video file selected: ${file.name}`);
      toast.success('Video file selected successfully!');
    }
  };

  const handleThumbnailUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadDetails(prev => ({ ...prev, thumbnail: file }));
      onLog(`Thumbnail selected: ${file.name}`);
      toast.success('Thumbnail selected successfully!');
    }
  };

  const handleUpload = async () => {
    if (!videoFile) {
      toast.error('Please select a video file first');
      return;
    }

    if (!uploadDetails.title.trim()) {
      toast.error('Please enter a video title');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    onLog('Starting YouTube upload...');

    // Simulate upload progress
    const uploadSteps = [
      'Preparing video file',
      'Uploading to YouTube',
      'Processing video',
      'Setting metadata',
      'Configuring privacy settings',
      'Generating auto-captions',
      'Adding tags',
      'Scheduling publication',
      'Upload complete'
    ];

    for (let i = 0; i < uploadSteps.length; i++) {
      onLog(`Upload step: ${uploadSteps[i]}`);
      
      // Simulate step duration
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const progress = ((i + 1) / uploadSteps.length) * 100;
      setUploadProgress(progress);
    }

    // Add to uploaded videos
    const newVideo: UploadedVideo = {
      id: `vid_${Date.now()}`,
      title: uploadDetails.title,
      uploadedAt: new Date().toLocaleString(),
      status: scheduleSettings.scheduleVideo ? 'scheduled' : 'uploaded',
      scheduledFor: scheduleSettings.scheduleVideo ? 
        `${new Date().toDateString()} ${scheduleSettings.timeSlot}` : undefined
    };

    setUploadedVideos(prev => [newVideo, ...prev]);
    setIsUploading(false);
    setUploadProgress(0);
    
    onLog('YouTube upload completed successfully');
    toast.success('Video uploaded successfully!');

    // Reset form
    setVideoFile(null);
    setUploadDetails({
      title: '',
      description: '',
      tags: '',
      visibility: 'public',
      category: 'Entertainment',
      thumbnail: null
    });
  };

  const generateAutoTags = () => {
    const autoTags = [
      'AI', 'Technology', 'Tutorial', 'Tips', 'Productivity',
      'Viral', 'Short', 'Trending', 'Educational', 'Entertainment'
    ];
    const selectedTags = autoTags.slice(0, 5).join(', ');
    setUploadDetails(prev => ({ ...prev, tags: selectedTags }));
    onLog('Auto-tags generated');
    toast.success('Auto-tags generated!');
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Upload Video</CardTitle>
            <CardDescription className="text-slate-400">
              Upload your video to MyAwesomeChannel
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label className="text-slate-300">Video File</Label>
              <Input
                type="file"
                accept="video/*"
                onChange={handleVideoUpload}
                className="bg-slate-700 border-slate-600 text-white file:bg-slate-600 file:text-white file:border-0"
              />
              {videoFile && (
                <p className="text-sm text-green-400 mt-1">
                  ✓ {videoFile.name} selected
                </p>
              )}
            </div>

            <div>
              <Label className="text-slate-300">Title</Label>
              <Input
                value={uploadDetails.title}
                onChange={(e) => setUploadDetails(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter video title"
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>

            <div>
              <Label className="text-slate-300">Description</Label>
              <Textarea
                value={uploadDetails.description}
                onChange={(e) => setUploadDetails(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter video description"
                className="bg-slate-700 border-slate-600 text-white"
                rows={4}
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-slate-300">Tags</Label>
                <Button 
                  size="sm" 
                  onClick={generateAutoTags}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Tag className="w-4 h-4 mr-2" />
                  Auto-Generate
                </Button>
              </div>
              <Input
                value={uploadDetails.tags}
                onChange={(e) => setUploadDetails(prev => ({ ...prev, tags: e.target.value }))}
                placeholder="Enter tags separated by commas"
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Visibility</Label>
                <Select 
                  value={uploadDetails.visibility} 
                  onValueChange={(value) => setUploadDetails(prev => ({ ...prev, visibility: value }))}
                >
                  <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-700 border-slate-600">
                    <SelectItem value="public" className="text-white">Public</SelectItem>
                    <SelectItem value="unlisted" className="text-white">Unlisted</SelectItem>
                    <SelectItem value="private" className="text-white">Private</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-slate-300">Category</Label>
                <Select 
                  value={uploadDetails.category} 
                  onValueChange={(value) => setUploadDetails(prev => ({ ...prev, category: value }))}
                >
                  <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-700 border-slate-600">
                    {categories.map(category => (
                      <SelectItem key={category} value={category} className="text-white">
                        {category}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label className="text-slate-300">Thumbnail (Optional)</Label>
              <Input
                type="file"
                accept="image/*"
                onChange={handleThumbnailUpload}
                className="bg-slate-700 border-slate-600 text-white file:bg-slate-600 file:text-white file:border-0"
              />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Schedule Settings</CardTitle>
            <CardDescription className="text-slate-400">
              Configure automatic scheduling and features
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                <Label className="text-slate-300">Schedule Video</Label>
              </div>
              <Switch
                checked={scheduleSettings.scheduleVideo}
                onCheckedChange={(checked) => setScheduleSettings(prev => ({ ...prev, scheduleVideo: checked }))}
              />
            </div>

            {scheduleSettings.scheduleVideo && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Time Slot</Label>
                  <Select 
                    value={scheduleSettings.timeSlot} 
                    onValueChange={(value) => setScheduleSettings(prev => ({ ...prev, timeSlot: value }))}
                  >
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      {timeSlots.map(slot => (
                        <SelectItem key={slot} value={slot} className="text-white">
                          {slot}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-slate-300">Timezone</Label>
                  <Input
                    value={scheduleSettings.timezone}
                    onChange={(e) => setScheduleSettings(prev => ({ ...prev, timezone: e.target.value }))}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Tag className="w-4 h-4 text-slate-400" />
                <Label className="text-slate-300">Auto Tags</Label>
              </div>
              <Switch
                checked={scheduleSettings.autoTags}
                onCheckedChange={(checked) => setScheduleSettings(prev => ({ ...prev, autoTags: checked }))}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Captions className="w-4 h-4 text-slate-400" />
                <Label className="text-slate-300">Auto Captions</Label>
              </div>
              <Switch
                checked={scheduleSettings.autoCaptions}
                onCheckedChange={(checked) => setScheduleSettings(prev => ({ ...prev, autoCaptions: checked }))}
              />
            </div>

            {isUploading && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-slate-300">Upload Progress</span>
                  <span className="text-slate-300">{Math.round(uploadProgress)}%</span>
                </div>
                <Progress value={uploadProgress} className="w-full" />
              </div>
            )}

            <Button 
              onClick={handleUpload}
              disabled={!videoFile || isUploading}
              className="w-full bg-red-600 hover:bg-red-700"
            >
              <Upload className="w-4 h-4 mr-2" />
              {isUploading ? 'Uploading...' : 'Upload to YouTube'}
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Upload History</CardTitle>
          <CardDescription className="text-slate-400">
            Track your uploaded videos and their status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {uploadedVideos.map((video) => (
              <div key={video.id} className="flex items-center justify-between p-4 bg-slate-700 rounded-lg">
                <div className="flex-1">
                  <h4 className="text-white font-medium">{video.title}</h4>
                  <p className="text-sm text-slate-400">
                    Uploaded: {video.uploadedAt}
                  </p>
                  {video.scheduledFor && (
                    <p className="text-sm text-blue-400">
                      Scheduled for: {video.scheduledFor}
                    </p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={
                    video.status === 'uploaded' ? 'default' :
                    video.status === 'scheduled' ? 'secondary' : 'outline'
                  }>
                    {video.status}
                  </Badge>
                  <Button size="sm" variant="outline" className="border-slate-600 text-slate-300">
                    View
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
