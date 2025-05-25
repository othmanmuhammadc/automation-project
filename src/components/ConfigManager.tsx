
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Save, Download, Upload } from 'lucide-react';
import { toast } from 'sonner';

interface ConfigManagerProps {
  onLog: (message: string) => void;
}

export const ConfigManager: React.FC<ConfigManagerProps> = ({ onLog }) => {
  const [config, setConfig] = useState({
    // AI Settings
    aiModel: 'chatgpt',
    apiKey: '',
    temperature: 0.7,
    maxTokens: 1000,
    
    // Video Settings
    voice: 'elfy',
    style: 'anime',
    aspectRatio: '9:16',
    quality: '1080p',
    fps: 60,
    
    // YouTube Settings
    channelName: 'MyAwesomeChannel',
    scheduleVideo: true,
    timeSlots: ['06:00', '12:00', '18:00', '00:00'],
    timezone: 'Asia/Cairo',
    autoTags: true,
    autoCaptions: true,
    
    // Automation Settings
    workflowMode: 'full_auto',
    repeatCount: 1,
    targetVideoCount: 5,
    headlessMode: false,
    
    // Browser Settings
    primaryBrowser: 'edge',
    fallbackBrowser: 'chrome',
    retryAttempts: 3
  });

  const [selectors, setSelectors] = useState({
    capcut: {
      loginButton: ['#login-btn', '.login-button', '[data-testid="login"]'],
      uploadButton: ['#upload', '.upload-btn', '[role="button"][aria-label="Upload"]'],
      generateButton: ['#generate', '.generate-btn', '.ai-generate']
    },
    youtube: {
      uploadButton: ['#upload-btn', '.upload-button', '[aria-label="Upload video"]'],
      titleInput: ['#title', '.title-input', '[aria-label="Title"]'],
      descriptionInput: ['#description', '.description-textarea', '[aria-label="Description"]']
    }
  });

  const handleConfigChange = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
    onLog(`Configuration updated: ${key} = ${value}`);
  };

  const handleSaveConfig = () => {
    const configData = JSON.stringify(config, null, 2);
    const blob = new Blob([configData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'customisation.json';
    a.click();
    
    onLog('Configuration saved to file');
    toast.success('Configuration saved successfully!');
  };

  const handleSaveSelectors = () => {
    const selectorsData = JSON.stringify(selectors, null, 2);
    const blob = new Blob([selectorsData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'selectors.json';
    a.click();
    
    onLog('Selectors saved to file');
    toast.success('Selectors saved successfully!');
  };

  return (
    <div className="max-w-4xl mx-auto">
      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-4 mb-6 bg-slate-800 border-slate-700">
          <TabsTrigger value="general" className="text-slate-300 data-[state=active]:text-white">
            General
          </TabsTrigger>
          <TabsTrigger value="ai" className="text-slate-300 data-[state=active]:text-white">
            AI Settings
          </TabsTrigger>
          <TabsTrigger value="video" className="text-slate-300 data-[state=active]:text-white">
            Video Settings
          </TabsTrigger>
          <TabsTrigger value="selectors" className="text-slate-300 data-[state=active]:text-white">
            Selectors
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">General Settings</CardTitle>
              <CardDescription className="text-slate-400">
                Configure basic automation parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Workflow Mode</Label>
                  <Select value={config.workflowMode} onValueChange={(value) => handleConfigChange('workflowMode', value)}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      <SelectItem value="full_auto" className="text-white">Full Auto</SelectItem>
                      <SelectItem value="script_only" className="text-white">Script Only</SelectItem>
                      <SelectItem value="video_only" className="text-white">Video Only</SelectItem>
                      <SelectItem value="upload_only" className="text-white">Upload Only</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label className="text-slate-300">Target Video Count</Label>
                  <Input
                    type="number"
                    value={config.targetVideoCount}
                    onChange={(e) => handleConfigChange('targetVideoCount', parseInt(e.target.value))}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <Label className="text-slate-300">Headless Mode</Label>
                <Switch
                  checked={config.headlessMode}
                  onCheckedChange={(checked) => handleConfigChange('headlessMode', checked)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Primary Browser</Label>
                  <Select value={config.primaryBrowser} onValueChange={(value) => handleConfigChange('primaryBrowser', value)}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      <SelectItem value="edge" className="text-white">Microsoft Edge</SelectItem>
                      <SelectItem value="chrome" className="text-white">Google Chrome</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label className="text-slate-300">Retry Attempts</Label>
                  <Input
                    type="number"
                    value={config.retryAttempts}
                    onChange={(e) => handleConfigChange('retryAttempts', parseInt(e.target.value))}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">AI Configuration</CardTitle>
              <CardDescription className="text-slate-400">
                Configure AI models and parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="text-slate-300">AI Model</Label>
                <Select value={config.aiModel} onValueChange={(value) => handleConfigChange('aiModel', value)}>
                  <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-700 border-slate-600">
                    <SelectItem value="chatgpt" className="text-white">ChatGPT</SelectItem>
                    <SelectItem value="grok" className="text-white">Grok</SelectItem>
                    <SelectItem value="gemini" className="text-white">Gemini</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-slate-300">API Key</Label>
                <Input
                  type="password"
                  value={config.apiKey}
                  onChange={(e) => handleConfigChange('apiKey', e.target.value)}
                  placeholder="Enter your API key"
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Temperature</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={config.temperature}
                    onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
                
                <div>
                  <Label className="text-slate-300">Max Tokens</Label>
                  <Input
                    type="number"
                    value={config.maxTokens}
                    onChange={(e) => handleConfigChange('maxTokens', parseInt(e.target.value))}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="video">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Video & YouTube Settings</CardTitle>
              <CardDescription className="text-slate-400">
                Configure video creation and upload parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Voice</Label>
                  <Input
                    value={config.voice}
                    onChange={(e) => handleConfigChange('voice', e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
                
                <div>
                  <Label className="text-slate-300">Style</Label>
                  <Input
                    value={config.style}
                    onChange={(e) => handleConfigChange('style', e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label className="text-slate-300">Aspect Ratio</Label>
                  <Select value={config.aspectRatio} onValueChange={(value) => handleConfigChange('aspectRatio', value)}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      <SelectItem value="9:16" className="text-white">9:16</SelectItem>
                      <SelectItem value="16:9" className="text-white">16:9</SelectItem>
                      <SelectItem value="1:1" className="text-white">1:1</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label className="text-slate-300">Quality</Label>
                  <Select value={config.quality} onValueChange={(value) => handleConfigChange('quality', value)}>
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
                  <Input
                    type="number"
                    value={config.fps}
                    onChange={(e) => handleConfigChange('fps', parseInt(e.target.value))}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>

              <div>
                <Label className="text-slate-300">YouTube Channel</Label>
                <Input
                  value={config.channelName}
                  onChange={(e) => handleConfigChange('channelName', e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>

              <div className="flex items-center justify-between">
                <Label className="text-slate-300">Schedule Videos</Label>
                <Switch
                  checked={config.scheduleVideo}
                  onCheckedChange={(checked) => handleConfigChange('scheduleVideo', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label className="text-slate-300">Auto Tags</Label>
                <Switch
                  checked={config.autoTags}
                  onCheckedChange={(checked) => handleConfigChange('autoTags', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label className="text-slate-300">Auto Captions</Label>
                <Switch
                  checked={config.autoCaptions}
                  onCheckedChange={(checked) => handleConfigChange('autoCaptions', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="selectors">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Element Selectors</CardTitle>
              <CardDescription className="text-slate-400">
                Configure XPath and CSS selectors for automation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="text-slate-300 text-lg mb-4 block">CapCut Selectors</Label>
                <div className="space-y-4">
                  <div>
                    <Label className="text-slate-300">Login Button</Label>
                    <Textarea
                      value={selectors.capcut.loginButton.join('\n')}
                      onChange={(e) => setSelectors(prev => ({
                        ...prev,
                        capcut: {
                          ...prev.capcut,
                          loginButton: e.target.value.split('\n').filter(s => s.trim())
                        }
                      }))}
                      className="bg-slate-700 border-slate-600 text-white"
                      rows={3}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-slate-300">Upload Button</Label>
                    <Textarea
                      value={selectors.capcut.uploadButton.join('\n')}
                      onChange={(e) => setSelectors(prev => ({
                        ...prev,
                        capcut: {
                          ...prev.capcut,
                          uploadButton: e.target.value.split('\n').filter(s => s.trim())
                        }
                      }))}
                      className="bg-slate-700 border-slate-600 text-white"
                      rows={3}
                    />
                  </div>
                </div>
              </div>

              <div>
                <Label className="text-slate-300 text-lg mb-4 block">YouTube Selectors</Label>
                <div className="space-y-4">
                  <div>
                    <Label className="text-slate-300">Upload Button</Label>
                    <Textarea
                      value={selectors.youtube.uploadButton.join('\n')}
                      onChange={(e) => setSelectors(prev => ({
                        ...prev,
                        youtube: {
                          ...prev.youtube,
                          uploadButton: e.target.value.split('\n').filter(s => s.trim())
                        }
                      }))}
                      className="bg-slate-700 border-slate-600 text-white"
                      rows={3}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-slate-300">Title Input</Label>
                    <Textarea
                      value={selectors.youtube.titleInput.join('\n')}
                      onChange={(e) => setSelectors(prev => ({
                        ...prev,
                        youtube: {
                          ...prev.youtube,
                          titleInput: e.target.value.split('\n').filter(s => s.trim())
                        }
                      }))}
                      className="bg-slate-700 border-slate-600 text-white"
                      rows={3}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex gap-4 mt-6">
        <Button onClick={handleSaveConfig} className="bg-blue-600 hover:bg-blue-700">
          <Save className="w-4 h-4 mr-2" />
          Save Configuration
        </Button>
        <Button onClick={handleSaveSelectors} className="bg-green-600 hover:bg-green-700">
          <Download className="w-4 h-4 mr-2" />
          Export Selectors
        </Button>
      </div>
    </div>
  );
};
