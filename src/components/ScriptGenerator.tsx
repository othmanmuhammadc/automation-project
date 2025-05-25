
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Wand2, Copy, Download, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface ScriptGeneratorProps {
  onLog: (message: string) => void;
}

export const ScriptGenerator: React.FC<ScriptGeneratorProps> = ({ onLog }) => {
  const [prompt, setPrompt] = useState('');
  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState('engaging');
  const [length, setLength] = useState('medium');
  const [generatedScript, setGeneratedScript] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState('');

  const samplePrompts = [
    "Create a viral YouTube short about productivity tips",
    "Generate a story about artificial intelligence",
    "Write a tutorial script about cooking basics",
    "Create an entertaining script about technology trends"
  ];

  const handleGenerate = async () => {
    if (!prompt.trim() && !topic.trim()) {
      toast.error('Please provide a prompt or topic');
      return;
    }

    setIsGenerating(true);
    onLog('Starting script generation...');

    // Simulate AI script generation
    await new Promise(resolve => setTimeout(resolve, 3000));

    const sampleScript = `# ${topic || 'Generated Video Script'}

## Hook (0-3 seconds)
Did you know that ${topic || 'this simple trick'} can completely change your life? Stay tuned to find out how!

## Main Content (3-45 seconds)
${prompt || 'Here\'s the main content of your script based on your prompt. This section would contain the core message, story, or information you want to convey to your audience.'}

Today, I'm going to share with you the most important insights about this topic. First, let's understand the basics...

[Continue with detailed explanation based on your prompt]

## Call to Action (45-60 seconds)
If you found this helpful, make sure to like this video and follow for more amazing content! What's your experience with this? Let me know in the comments below!

## Tags
${keywords.join(', ')}

## Estimated Duration: 60 seconds
## Tone: ${tone}
## Length: ${length}`;

    setGeneratedScript(sampleScript);
    setIsGenerating(false);
    onLog('Script generation completed successfully');
    toast.success('Script generated successfully!');
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedScript);
    toast.success('Script copied to clipboard!');
    onLog('Script copied to clipboard');
  };

  const handleDownload = () => {
    const blob = new Blob([generatedScript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `script_${Date.now()}.txt`;
    a.click();
    
    onLog('Script downloaded to file');
    toast.success('Script downloaded successfully!');
  };

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !keywords.includes(newKeyword.trim())) {
      setKeywords([...keywords, newKeyword.trim()]);
      setNewKeyword('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setKeywords(keywords.filter(k => k !== keyword));
  };

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Script Generator</CardTitle>
          <CardDescription className="text-slate-400">
            Generate AI-powered scripts for your videos
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="text-slate-300">Topic/Subject</Label>
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter your video topic"
              className="bg-slate-700 border-slate-600 text-white"
            />
          </div>

          <div>
            <Label className="text-slate-300">Detailed Prompt</Label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe what you want your script to be about..."
              className="bg-slate-700 border-slate-600 text-white"
              rows={4}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">Tone</Label>
              <Select value={tone} onValueChange={setTone}>
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="engaging" className="text-white">Engaging</SelectItem>
                  <SelectItem value="professional" className="text-white">Professional</SelectItem>
                  <SelectItem value="casual" className="text-white">Casual</SelectItem>
                  <SelectItem value="humorous" className="text-white">Humorous</SelectItem>
                  <SelectItem value="educational" className="text-white">Educational</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-slate-300">Length</Label>
              <Select value={length} onValueChange={setLength}>
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="short" className="text-white">Short (30s)</SelectItem>
                  <SelectItem value="medium" className="text-white">Medium (60s)</SelectItem>
                  <SelectItem value="long" className="text-white">Long (90s)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label className="text-slate-300">Keywords/Tags</Label>
            <div className="flex gap-2 mb-2">
              <Input
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                placeholder="Add keyword"
                className="bg-slate-700 border-slate-600 text-white"
                onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
              />
              <Button onClick={handleAddKeyword} size="sm">Add</Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword, index) => (
                <Badge 
                  key={index} 
                  variant="secondary" 
                  className="cursor-pointer"
                  onClick={() => handleRemoveKeyword(keyword)}
                >
                  {keyword} ×
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <Label className="text-slate-300 mb-2 block">Sample Prompts</Label>
            <div className="space-y-2">
              {samplePrompts.map((sample, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => setPrompt(sample)}
                  className="w-full text-left justify-start border-slate-600 text-slate-300 hover:text-white"
                >
                  {sample}
                </Button>
              ))}
            </div>
          </div>

          <Button 
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-purple-600 hover:bg-purple-700"
          >
            {isGenerating ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Wand2 className="w-4 h-4 mr-2" />
            )}
            {isGenerating ? 'Generating...' : 'Generate Script'}
          </Button>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Generated Script</CardTitle>
          <CardDescription className="text-slate-400">
            Your AI-generated video script
          </CardDescription>
        </CardHeader>
        <CardContent>
          {generatedScript ? (
            <div className="space-y-4">
              <Textarea
                value={generatedScript}
                onChange={(e) => setGeneratedScript(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white min-h-[400px]"
                placeholder="Your generated script will appear here..."
              />
              
              <div className="flex gap-2">
                <Button onClick={handleCopy} size="sm" variant="outline" className="border-slate-600 text-slate-300">
                  <Copy className="w-4 h-4 mr-2" />
                  Copy
                </Button>
                <Button onClick={handleDownload} size="sm" variant="outline" className="border-slate-600 text-slate-300">
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">
              <Wand2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Your generated script will appear here</p>
              <p className="text-sm">Fill in the form and click "Generate Script" to get started</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
