import { Bell, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { authApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export function TopBar() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [user, setUser] = useState<{ username: string } | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    // Get current user from localStorage
    const currentUser = authApi.getCurrentUser();
    setUser(currentUser);
  }, []);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    
    try {
      const response = await authApi.logout();
      
      if (response.success) {
        toast({
          title: "Logged Out",
          description: "You have been successfully logged out.",
        });
        
        // Redirect to login page
        setTimeout(() => {
          navigate("/login", { replace: true });
        }, 500);
      }
    } catch (error: any) {
      console.error("Logout error:", error);
      // Even if there's an error, clear local storage and redirect
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      toast({
        title: "Logged Out",
        description: "You have been logged out.",
      });
      navigate("/login", { replace: true });
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleSettings = () => {
    navigate("/settings");
  };

  const handleProfile = () => {
    // Navigate to profile page (if exists) or settings
    navigate("/settings");
  };

  return (
    <header className="h-16 border-b border-border bg-card flex items-center justify-between px-4">
      <div className="flex items-center gap-4">
        {/* Desktop trigger on the left */}
        <SidebarTrigger className="hidden md:inline-flex" />
        <div className="text-sm text-muted-foreground">
          <span className="hidden sm:inline">Welcome back, </span>
          <span className="font-medium text-foreground">
            {user?.username || "User"}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Mobile burger on the right */}
        <SidebarTrigger className="md:hidden order-last" aria-label="Open menu" />
        
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-destructive" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <User className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleProfile}>Profile</DropdownMenuItem>
            <DropdownMenuItem onClick={handleSettings}>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="text-destructive focus:text-destructive"
            >
              {isLoggingOut ? "Logging out..." : "Logout"}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
