import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Settings as SettingsIcon, Users, Database, Bell, Building2, Mail, Shield } from "lucide-react";

export default function Settings() {
  return (
    <div className="page-shell">
      {/* Header */}
      <div>
        <h1 className="page-title text-3xl sm:text-4xl text-foreground">Settings</h1>
        <p className="subtle-text mt-1">Configure system preferences and defaults</p>
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="bg-card border shadow-sm">
          <TabsTrigger value="general" className="gap-2">
            <SettingsIcon className="h-4 w-4" />
            General
          </TabsTrigger>
          <TabsTrigger value="users" className="gap-2">
            <Users className="h-4 w-4" />
            Users
          </TabsTrigger>
          <TabsTrigger value="data" className="gap-2">
            <Database className="h-4 w-4" />
            Data Processing
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="general" className="space-y-6">
          <Card className="border-0 shadow-md">
            <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary-light">
                  <Building2 className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Company Information</CardTitle>
                  <CardDescription>Basic configuration for the application</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="space-y-2">
                <Label>Company Name</Label>
                <Input placeholder="Vardaan Data Sciences" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Default Currency</Label>
                  <Select defaultValue="inr">
                    <SelectTrigger>
                      <SelectValue placeholder="Select currency" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="inr">INR (₹)</SelectItem>
                      <SelectItem value="usd">USD ($)</SelectItem>
                      <SelectItem value="eur">EUR (€)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Financial Year Start</Label>
                  <Select defaultValue="april">
                    <SelectTrigger>
                      <SelectValue placeholder="Select month" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="january">January</SelectItem>
                      <SelectItem value="april">April</SelectItem>
                      <SelectItem value="july">July</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="pt-4">
                <Button className="bg-gradient-primary text-white shadow-primary">
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* User Management */}
        <TabsContent value="users" className="space-y-6">
          <Card className="border-0 shadow-md">
            <CardHeader className="border-b bg-gradient-to-r from-accent/5 to-transparent">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-accent-light">
                  <Users className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <CardTitle>User Management</CardTitle>
                  <CardDescription>Manage users and their access levels</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="flex items-center justify-between py-4 px-4 rounded-lg bg-gradient-to-r from-primary/5 to-transparent border border-border/50 hover:shadow-md transition-all">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary-light">
                    <Shield className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Admin Users</p>
                    <p className="text-sm text-muted-foreground">Full access to all features</p>
                  </div>
                </div>
                <Button variant="outline" size="sm">Manage</Button>
              </div>

              <div className="flex items-center justify-between py-4 px-4 rounded-lg bg-gradient-to-r from-accent/5 to-transparent border border-border/50 hover:shadow-md transition-all">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-accent-light">
                    <Users className="h-5 w-5 text-accent" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Analyst Users</p>
                    <p className="text-sm text-muted-foreground">View and analyze data</p>
                  </div>
                </div>
                <Button variant="outline" size="sm">Manage</Button>
              </div>

              <div className="flex items-center justify-between py-4 px-4 rounded-lg bg-gradient-to-r from-success/5 to-transparent border border-border/50 hover:shadow-md transition-all">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-success-light">
                    <Users className="h-5 w-5 text-success" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Viewer Users</p>
                    <p className="text-sm text-muted-foreground">Read-only access</p>
                  </div>
                </div>
                <Button variant="outline" size="sm">Manage</Button>
              </div>

              <div className="pt-2">
                <Button className="w-full bg-gradient-accent text-white shadow-accent">Add New User</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Data Processing */}
        <TabsContent value="data" className="space-y-6">
          <Card className="border-0 shadow-md">
            <CardHeader className="border-b bg-gradient-to-r from-success/5 to-transparent">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-success-light">
                  <Database className="h-5 w-5 text-success" />
                </div>
                <div>
                  <CardTitle>Data Processing Configuration</CardTitle>
                  <CardDescription>Configure how uploaded data is processed</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="space-y-2">
                <Label>Default Account Mapping</Label>
                <Select defaultValue="standard">
                  <SelectTrigger>
                    <SelectValue placeholder="Select mapping" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Standard Indian GAAP</SelectItem>
                    <SelectItem value="ifrs">IFRS</SelectItem>
                    <SelectItem value="custom">Custom Mapping</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/5 to-transparent border border-border/50">
                  <div className="space-y-0.5">
                    <Label>Strict Validation</Label>
                    <p className="text-sm text-muted-foreground">Reject files with validation errors</p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-accent/5 to-transparent border border-border/50">
                  <div className="space-y-0.5">
                    <Label>Auto-process Uploads</Label>
                    <p className="text-sm text-muted-foreground">Automatically process files after upload</p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-warning/5 to-transparent border border-border/50">
                  <div className="space-y-0.5">
                    <Label>Overwrite Existing Data</Label>
                    <p className="text-sm text-muted-foreground">Replace data for duplicate periods</p>
                  </div>
                  <Switch />
                </div>
              </div>

              <div className="pt-4">
                <Button className="bg-gradient-success text-white">Save Configuration</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-6">
          <Card className="border-0 shadow-md">
            <CardHeader className="border-b bg-gradient-to-r from-info/5 to-transparent">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-info-light">
                  <Bell className="h-5 w-5 text-info" />
                </div>
                <div>
                  <CardTitle>Notification Preferences</CardTitle>
                  <CardDescription>Configure how you receive alerts and updates</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/5 to-transparent border border-border/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary-light">
                    <Mail className="h-5 w-5 text-primary" />
                  </div>
                  <div className="space-y-0.5">
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive alerts for uploads and processing</p>
                  </div>
                </div>
                <Switch />
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-success/5 to-transparent border border-border/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-success-light">
                    <Bell className="h-5 w-5 text-success" />
                  </div>
                  <div className="space-y-0.5">
                    <Label>System Alerts</Label>
                    <p className="text-sm text-muted-foreground">Important system notifications</p>
                  </div>
                </div>
                <Switch defaultChecked />
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-warning/5 to-transparent border border-border/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-warning-light">
                    <Bell className="h-5 w-5 text-warning" />
                  </div>
                  <div className="space-y-0.5">
                    <Label>Processing Failures</Label>
                    <p className="text-sm text-muted-foreground">Alerts when file processing fails</p>
                  </div>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
