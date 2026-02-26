import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { MainLayout } from "./components/layout/MainLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import Entities from "./pages/Entities";
import Upload from "./pages/Upload";
import StructuredData from "./pages/StructuredData";
import CodeMasterPage from "./pages/CodeMaster";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          {/* Login page - default route */}
          <Route path="/login" element={<Login />} />
          
          {/* Redirect root to login (will redirect to dashboard if authenticated) */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* Protected routes - require authentication */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <MainLayout><Dashboard /></MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/entities"
            element={
              <ProtectedRoute>
                <MainLayout><Entities /></MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <MainLayout><Upload /></MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/structured-data"
            element={
              <ProtectedRoute>
                <MainLayout><StructuredData /></MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/code-master"
            element={
              <ProtectedRoute>
                <MainLayout><CodeMasterPage /></MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <MainLayout><Reports /></MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <MainLayout><Settings /></MainLayout>
              </ProtectedRoute>
            }
          />
          
          {/* 404 Not Found */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
