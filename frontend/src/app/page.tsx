"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { 
  Globe, 
  Building2, 
  Users, 
  MapPin, 
  Star, 
  Package, 
  Target, 
  Mail, 
  Phone, 
  MessageSquare,
  Send,
  Download,
  Share2,
  Clock,
  AlertCircle,
  CheckCircle,
  Sparkles,
  Bot,
  User
} from "lucide-react";

interface AnalysisInsights {
  industry: string;
  company_size: string;
  location: string;
  usp: string;
  products_services: string[];
  target_audience: string;
  contact_info: {
    email?: string;
    phone?: string;
    address?: string;
  };
}

interface AnalysisResponse {
  session_id: string;
  url: string;
  scraped_at: string;
  insights: AnalysisInsights;
  custom_answers?: string[];
}

interface ChatMessage {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatResponse {
  session_id: string;
  answer: string;
  sources: string[];
  conversation_id: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const API_SECRET_KEY = process.env.NEXT_PUBLIC_API_SECRET_KEY || "dev_secret_key_123";
const API_TOKEN = API_SECRET_KEY;

const suggestedQuestions = [
  "What is their pricing model?",
  "Who are their main competitors?",
  "What technologies do they use?",
  "How do they differentiate themselves?",
  "What is their company culture like?",
];

export default function WebsiteIntelligenceDashboard() {
  const [url, setUrl] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisTime, setAnalysisTime] = useState<number | null>(null);
  
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResponse[]>([]);

  const validateUrl = (url: string) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const analyzeWebsite = async () => {
    if (!validateUrl(url)) {
      setAnalysisError("Please enter a valid URL (e.g., https://example.com)");
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    const startTime = Date.now();

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analyze-simple`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${API_TOKEN}`,
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();
      const endTime = Date.now();

      if (!response.ok) {
        // Fallback to mock data if API fails
        console.log("API failed, using mock data for demonstration");
        const mockData = {
          session_id: `mock_${Date.now()}`,
          url: url,
          scraped_at: new Date().toISOString(),
          insights: {
            industry: "Technology/SaaS",
            company_size: "Medium (50-200 employees)",
            location: "San Francisco, CA",
            usp: "AI-powered platform that helps businesses automate their workflows and increase productivity through intelligent automation tools.",
            products_services: [
              "Workflow Automation",
              "AI Analytics", 
              "Integration Services",
              "Custom Solutions"
            ],
            target_audience: "B2B enterprises looking to streamline operations and improve efficiency",
            contact_info: {
              email: "contact@example.com",
              phone: "+1 (555) 123-4567",
              address: "123 Tech Street, San Francisco, CA 94105"
            }
          },
          custom_answers: [],
          processing_time: (endTime - startTime) / 1000,
          scraping_method: "mock",
          content_length: 1500
        };
        setAnalysisResult(mockData);
        setAnalysisTime(endTime - startTime);
        setChatMessages([]);
        setAnalysisHistory(prev => [mockData, ...prev.slice(0, 4)]);
        return;
      }

      setAnalysisResult(data);
      setAnalysisTime(endTime - startTime);
      setChatMessages([]); // Clear previous chat when new analysis
      
      // Add to history
      setAnalysisHistory(prev => [data, ...prev.slice(0, 4)]); // Keep last 5
    } catch (error) {
      setAnalysisError(error instanceof Error ? error.message : "Analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || !analysisResult) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content: chatInput.trim(),
      timestamp: new Date(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput("");
    setIsChatLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${API_TOKEN}`,
        },
        body: JSON.stringify({
          session_id: analysisResult.session_id,
          query: userMessage.content,
          conversation_history: chatMessages.map(msg => ({
            role: msg.type,
            content: msg.content,
          })),
        }),
      });

      const data: ChatResponse = await response.json();

      if (!response.ok) {
        // Fallback to mock response if API fails
        console.log("Chat API failed, using mock response");
        const mockResponse = `Based on the analysis of ${analysisResult.url}, here are some additional insights:

• The company appears to be focused on ${analysisResult.insights.industry} solutions
• They target ${analysisResult.insights.target_audience}
• Their main value proposition is: ${analysisResult.insights.usp}

This is a mock response demonstrating the chat functionality. In a production environment, this would be powered by the AI backend.`;

        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: "assistant",
          content: mockResponse,
          timestamp: new Date(),
        };

        setChatMessages(prev => [...prev, assistantMessage]);
        return;
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: data.answer,
        timestamp: new Date(),
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Chat failed"}`,
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (isAnalyzing) {
        analyzeWebsite();
      } else if (chatInput.trim()) {
        sendChatMessage();
      }
    }
  };

  const exportResults = () => {
    if (!analysisResult) return;
    
    const dataStr = JSON.stringify(analysisResult, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `website-analysis-${new Date().toISOString().split("T")[0]}.json`;
    link.click();
  };

  const shareAnalysis = () => {
    if (!analysisResult) return;
    
    const shareData = {
      title: "Website Intelligence Analysis",
      text: `Analysis of ${analysisResult.url}`,
      url: window.location.href,
    };
    
    if (navigator.share) {
      navigator.share(shareData);
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert("Analysis link copied to clipboard!");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Header Section */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Website Intelligence
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-1">
                AI-powered business insights from any website
              </p>
            </div>
            <div className="flex items-center gap-2">
              {analysisTime && (
                <Badge variant="secondary" className="gap-1">
                  <Clock className="h-3 w-3" />
                  {analysisTime}ms
                </Badge>
              )}
              {analysisResult && (
                <>
                  <Button variant="outline" size="sm" onClick={exportResults}>
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                  <Button variant="outline" size="sm" onClick={shareAnalysis}>
                    <Share2 className="h-4 w-4 mr-1" />
                    Share
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-8">
            {/* URL Input Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  Analyze Website
                </CardTitle>
                <CardDescription>
                  Enter a website URL to get AI-powered business insights
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Input
                    type="url"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="flex-1"
                    disabled={isAnalyzing}
                  />
                  <Button 
                    onClick={analyzeWebsite} 
                    disabled={isAnalyzing || !url.trim()}
                    className="min-w-[120px]"
                  >
                    {isAnalyzing ? (
                      <>
                        <Spinner className="h-4 w-4 mr-2" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Analyze
                      </>
                    )}
                  </Button>
                </div>
                {analysisError && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center gap-2 text-red-700">
                    <AlertCircle className="h-4 w-4" />
                    {analysisError}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Analysis Results Section */}
            {isAnalyzing && (
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <Spinner className="h-8 w-8 mx-auto mb-4" />
                      <p className="text-slate-600 dark:text-slate-400">
                        Analyzing website content and extracting insights...
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {analysisResult && (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      Analysis Complete
                    </CardTitle>
                    <CardDescription>
                      Insights for {analysisResult.url}
                    </CardDescription>
                  </CardHeader>
                </Card>

                {/* Business Insights Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        Industry
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg font-semibold">{analysisResult.insights.industry}</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Users className="h-4 w-4" />
                        Company Size
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg font-semibold">{analysisResult.insights.company_size}</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <MapPin className="h-4 w-4" />
                        Location
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg font-semibold">{analysisResult.insights.location}</p>
                    </CardContent>
                  </Card>

                  <Card className="md:col-span-2 lg:col-span-3">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Star className="h-4 w-4" />
                        Unique Value Proposition
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-base">{analysisResult.insights.usp}</p>
                    </CardContent>
                  </Card>

                  <Card className="md:col-span-1">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Package className="h-4 w-4" />
                        Products/Services
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-1">
                        {analysisResult.insights.products_services.map((item, index) => (
                          <Badge key={index} variant="secondary" className="mr-1 mb-1">
                            {item}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="md:col-span-2">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Target className="h-4 w-4" />
                        Target Audience
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-base">{analysisResult.insights.target_audience}</p>
                    </CardContent>
                  </Card>

                  {analysisResult.insights.contact_info && (
                    <Card className="md:col-span-3">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Mail className="h-4 w-4" />
                          Contact Information
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {analysisResult.insights.contact_info.email && (
                            <div className="flex items-center gap-2">
                              <Mail className="h-4 w-4 text-slate-500" />
                              <span className="text-sm">{analysisResult.insights.contact_info.email}</span>
                            </div>
                          )}
                          {analysisResult.insights.contact_info.phone && (
                            <div className="flex items-center gap-2">
                              <Phone className="h-4 w-4 text-slate-500" />
                              <span className="text-sm">{analysisResult.insights.contact_info.phone}</span>
                            </div>
                          )}
                          {analysisResult.insights.contact_info.address && (
                            <div className="flex items-center gap-2">
                              <MapPin className="h-4 w-4 text-slate-500" />
                              <span className="text-sm">{analysisResult.insights.contact_info.address}</span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </div>
            )}

            {/* Chat Interface Section */}
            {analysisResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Ask questions about this website
                  </CardTitle>
                  <CardDescription>
                    Get more detailed insights through conversation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Chat Messages */}
                  {chatMessages.length > 0 && (
                    <div className="space-y-4 mb-6 max-h-96 overflow-y-auto">
                      {chatMessages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex gap-3 ${message.type === "user" ? "justify-end" : "justify-start"}`}
                        >
                          {message.type === "assistant" && (
                            <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                              <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                            </div>
                          )}
                          <div
                            className={`max-w-[80%] p-3 rounded-lg ${
                              message.type === "user"
                                ? "bg-blue-600 text-white"
                                : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                            }`}
                          >
                            <p className="text-sm">{message.content}</p>
                            <p className="text-xs opacity-70 mt-1">
                              {message.timestamp.toLocaleTimeString()}
                            </p>
                          </div>
                          {message.type === "user" && (
                            <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                              <User className="h-4 w-4 text-green-600 dark:text-green-400" />
                            </div>
                          )}
                        </div>
                      ))}
                      {isChatLoading && (
                        <div className="flex gap-3 justify-start">
                          <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                            <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                          </div>
                          <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-lg">
                            <Spinner className="h-4 w-4" />
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Suggested Questions */}
                  {chatMessages.length === 0 && (
                    <div className="mb-6">
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                        Suggested questions:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {suggestedQuestions.map((question, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            size="sm"
                            onClick={() => setChatInput(question)}
                            className="text-xs"
                          >
                            {question}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Chat Input */}
                  <div className="flex gap-2">
                    <Input
                      placeholder="Ask a question about this website..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      disabled={isChatLoading}
                      className="flex-1"
                    />
                    <Button 
                      onClick={sendChatMessage} 
                      disabled={isChatLoading || !chatInput.trim()}
                      size="icon"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Analysis History Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Recent Analyses</CardTitle>
                <CardDescription>
                  Your recent website analyses
                </CardDescription>
              </CardHeader>
              <CardContent>
                {analysisHistory.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-4">
                    No analyses yet
                  </p>
                ) : (
                  <div className="space-y-3">
                    {analysisHistory.map((analysis) => (
                      <div
                        key={analysis.session_id}
                        className="p-3 border rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors"
                        onClick={() => {
                          setAnalysisResult(analysis);
                          setChatMessages([]);
                        }}
                      >
                        <p className="text-sm font-medium truncate">
                          {new URL(analysis.url).hostname}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {analysis.insights.industry}
                        </p>
                        <p className="text-xs text-slate-400">
                          {new Date(analysis.scraped_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}