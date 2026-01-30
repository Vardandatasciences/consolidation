import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  TrendingUp, 
  Shield, 
  Lock, 
  Mail, 
  User, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  Building2,
  BarChart3,
  Database,
  PieChart,
  FileText,
  Zap,
  Globe,
  Users
} from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { authApi, testApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });
  const [connectionStatus, setConnectionStatus] = useState<"checking" | "connected" | "error">("checking");
  const [mounted, setMounted] = useState(false);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (authApi.isAuthenticated()) {
      const from = (location.state as any)?.from?.pathname || "/dashboard";
      navigate(from, { replace: true });
    }
  }, [navigate, location]);

  // Mount animation
  useEffect(() => {
    setMounted(true);
  }, []);

  // Check backend connection on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await testApi.test();
        if (response.success) {
          setConnectionStatus("connected");
        } else {
          setConnectionStatus("error");
        }
      } catch (error) {
        setConnectionStatus("error");
      }
    };
    
    checkConnection();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.id]: e.target.value,
    });
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      toast({
        title: "Error",
        description: "Please enter both username and password",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      console.log("[Login] Attempting login for:", formData.username);
      
      const response = await authApi.login({
        username: formData.username,
        password: formData.password,
      });

      console.log("[Login] Response received:", response);

      if (response.success && response.data) {
        toast({
          title: "Success",
          description: `Welcome back, ${response.data.user.username}!`,
        });
        
        // Redirect to dashboard or the page user was trying to access
        const from = (location.state as any)?.from?.pathname || "/dashboard";
        setTimeout(() => {
          navigate(from, { replace: true });
        }, 500);
      } else {
        throw new Error(response.message || "Login failed. Please check your credentials.");
      }
    } catch (error: any) {
      console.error("[Login] Error:", error);
      
      // Determine error message
      let errorMessage = "Invalid credentials. Please try again.";
      
      if (error.message) {
        if (error.message.includes("connect to server")) {
          errorMessage = "Cannot connect to server. Please ensure the backend is running.";
        } else if (error.message.includes("credentials") || error.message.includes("Invalid")) {
          errorMessage = "Invalid username or password. Please try again.";
        } else {
          errorMessage = error.message;
        }
      }
      
      toast({
        title: "Login Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const features = [
    {
      icon: BarChart3,
      title: "Advanced Analytics",
      description: "Real-time financial insights and comprehensive reporting"
    },
    {
      icon: Database,
      title: "Multi-Entity Management",
      description: "Manage multiple entities from a single unified platform"
    },
    {
      icon: PieChart,
      title: "Data Visualization",
      description: "Interactive charts and graphs for better decision making"
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "Bank-level encryption and secure data handling"
    }
  ];

  return (
    <div className="min-h-screen flex relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-50">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      {/* Decorative Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] opacity-40" />

      {/* Two Column Layout */}
      <div className="w-full flex flex-col lg:flex-row relative z-10">
        {/* Left Side - Content */}
        <div className={`hidden lg:flex lg:w-1/2 flex-col justify-center px-12 xl:px-16 2xl:px-24 py-12 transition-all duration-700 ${
          mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'
        }`}>
          <div className="max-w-xl space-y-8">
            {/* Logo and Branding */}
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-accent/20 rounded-2xl blur-xl animate-pulse" />
                  <div className="relative p-4 bg-gradient-to-br from-primary/10 via-primary/5 to-accent/10 rounded-2xl border border-primary/20">
                    <div className="flex items-center justify-center gap-2">
                      <TrendingUp className="h-8 w-8 text-primary animate-pulse" style={{ animationDuration: '2s' }} />
                      <BarChart3 className="h-6 w-6 text-accent" />
                    </div>
                  </div>
                </div>
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-primary to-accent bg-clip-text text-transparent">
                    Financial Analyzer
                  </h1>
                  <p className="text-sm text-muted-foreground mt-1">Vardaan Data Sciences</p>
                </div>
              </div>

              <div className="space-y-3">
                <h2 className="text-3xl font-bold text-foreground">
                  Multi-Entity Financial Intelligence Platform
                </h2>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  Transform your financial data into actionable insights. Manage multiple entities, 
                  analyze trends, and make data-driven decisions with confidence.
                </p>
              </div>
            </div>

            {/* Features Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div
                    key={index}
                    className="group p-4 rounded-lg bg-card/50 backdrop-blur-sm border border-border/50 hover:border-primary/30 hover:bg-card/70 transition-all duration-300 hover:shadow-md"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 space-y-1">
                        <h3 className="font-semibold text-sm text-foreground">{feature.title}</h3>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {feature.description}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Trust Indicators */}
            <div className="flex items-center gap-6 pt-4 border-t border-border/50">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary/70" />
                <span className="text-sm text-muted-foreground font-medium">Enterprise Security</span>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-primary/70" />
                <span className="text-sm text-muted-foreground font-medium">Cloud-Based</span>
              </div>
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary/70" />
                <span className="text-sm text-muted-foreground font-medium">Multi-User</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className={`w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-8 lg:p-12 xl:p-16 transition-all duration-700 ${
          mounted ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'
        }`}>
          <div className="w-full max-w-md">
            <Card className="backdrop-blur-sm bg-card/95 border-border/50 shadow-2xl">
              <CardHeader className="space-y-4 pb-6">
                {/* Mobile Logo - Only visible on small screens */}
                <div className="lg:hidden flex justify-center mb-4">
                  <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-accent/20 rounded-2xl blur-xl animate-pulse" />
                    <div className="relative p-3 bg-gradient-to-br from-primary/10 via-primary/5 to-accent/10 rounded-2xl border border-primary/20">
                      <div className="flex items-center justify-center gap-2">
                        <TrendingUp className="h-6 w-6 text-primary animate-pulse" style={{ animationDuration: '2s' }} />
                        <BarChart3 className="h-5 w-5 text-accent" />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 text-center lg:text-left">
                  <CardTitle className="text-2xl lg:text-3xl font-bold">
                    Welcome Back
                  </CardTitle>
                  <CardDescription className="text-base">
                    Sign in to access your financial dashboard
                  </CardDescription>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Connection Status Indicator */}
                {connectionStatus !== "checking" && (
                  <div className={`p-3 rounded-lg text-xs flex items-center justify-center gap-2 transition-all duration-300 ${
                    connectionStatus === "connected" 
                      ? "bg-success-light text-success border border-success/30" 
                      : "bg-destructive/10 text-destructive border border-destructive/30"
                  }`}>
                    {connectionStatus === "connected" ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 animate-pulse" />
                        <span>Backend connected</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-4 w-4" />
                        <span>Cannot connect to backend. Please ensure the server is running.</span>
                      </>
                    )}
                  </div>
                )}
                
                <form onSubmit={handleLogin} className="space-y-5">
                  {/* Username Field */}
                  <div className="space-y-2">
                    <Label htmlFor="username" className="text-sm font-medium flex items-center gap-2">
                      <User className="h-3.5 w-3.5 text-muted-foreground" />
                      Email / Username
                    </Label>
                    <div className="relative group">
                      <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors">
                        <Mail className="h-4 w-4" />
                      </div>
                      <Input 
                        id="username" 
                        type="text" 
                        placeholder="Enter your username or email"
                        value={formData.username}
                        onChange={handleInputChange}
                        disabled={isLoading}
                        required
                        className="pl-10 h-11 transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  </div>
                  
                  {/* Password Field */}
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-sm font-medium flex items-center gap-2">
                      <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                      Password
                    </Label>
                    <div className="relative group">
                      <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors">
                        <Lock className="h-4 w-4" />
                      </div>
                      <Input 
                        id="password" 
                        type="password" 
                        placeholder="Enter your password"
                        value={formData.password}
                        onChange={handleInputChange}
                        disabled={isLoading}
                        required
                        className="pl-10 h-11 transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  </div>

                  {/* Login Button */}
                  <Button 
                    type="submit" 
                    className="w-full h-11 text-base font-semibold bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]" 
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Authenticating...
                      </>
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-2" />
                        Sign In
                      </>
                    )}
                  </Button>

                  {/* Forgot Password */}
                  <div className="text-center pt-2">
                    <Button 
                      variant="link" 
                      className="text-sm text-muted-foreground hover:text-primary transition-colors"
                      type="button"
                    >
                      Forgot Password?
                    </Button>
                  </div>
                </form>

                {/* Footer */}
                <div className="mt-8 pt-6 border-t border-border/50">
                  <div className="flex items-center justify-center gap-4 mb-3">
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Building2 className="h-3.5 w-3.5" />
                      <span>Vardaan Data Sciences</span>
                    </div>
                  </div>
                  <p className="text-xs text-center text-muted-foreground/80">
                    © 2024 Vardaan Data Sciences. All rights reserved.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
