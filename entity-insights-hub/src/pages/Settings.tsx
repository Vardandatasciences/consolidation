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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Settings as SettingsIcon, Users, Database, Bell, Building2, Mail, Shield, Calendar, Plus, Edit, Trash2, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { financialYearMasterApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

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
          <TabsTrigger value="master-data" className="gap-2">
            <Calendar className="h-4 w-4" />
            Master Data
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

        {/* Master Data */}
        <TabsContent value="master-data" className="space-y-6">
          <FinancialYearMaster />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Financial Year Master Component
function FinancialYearMaster() {
  const { toast } = useToast();
  const [financialYears, setFinancialYears] = useState<Array<{
    id: number;
    financial_year: string;
    start_date: string;
    end_date: string;
    is_active: boolean;
    description: string | null;
    created_at: string;
    updated_at: string;
  }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({
    financial_year: "",
    start_date: "",
    end_date: "",
    is_active: true,
    description: "",
  });

  useEffect(() => {
    loadFinancialYears();
  }, []);

  const loadFinancialYears = async () => {
    try {
      setIsLoading(true);
      const res = await financialYearMasterApi.list();
      if (res.success && res.data?.financial_years) {
        setFinancialYears(res.data.financial_years);
      }
    } catch (e: any) {
      toast({
        title: "Failed to load financial years",
        description: e.message || "Could not fetch financial years",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingId(null);
    setForm({
      financial_year: "",
      start_date: "",
      end_date: "",
      is_active: true,
      description: "",
    });
    setOpen(true);
  };

  const handleEdit = (fy: typeof financialYears[0]) => {
    setEditingId(fy.id);
    // Format dates for HTML date input (YYYY-MM-DD)
    const formatDateForInput = (dateStr: string) => {
      if (!dateStr) return "";
      try {
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
      } catch {
        return dateStr.split("T")[0]; // Fallback: take date part if it includes time
      }
    };
    setForm({
      financial_year: fy.financial_year,
      start_date: formatDateForInput(fy.start_date),
      end_date: formatDateForInput(fy.end_date),
      is_active: fy.is_active,
      description: fy.description || "",
    });
    setOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to deactivate this financial year?")) {
      return;
    }

    try {
      const res = await financialYearMasterApi.delete(id);
      if (res.success) {
        toast({ title: "Financial year deactivated successfully" });
        loadFinancialYears();
      }
    } catch (e: any) {
      toast({
        title: "Delete failed",
        description: e.message || "Unable to deactivate financial year",
        variant: "destructive",
      });
    }
  };

  const handleSubmit = async () => {
    if (!form.financial_year || !form.start_date || !form.end_date) {
      toast({
        title: "Missing fields",
        description: "Financial year, start date, and end date are required",
        variant: "destructive",
      });
      return;
    }

    // Ensure dates are in YYYY-MM-DD format
    const formatDateForAPI = (dateStr: string) => {
      if (!dateStr) return "";
      // If already in YYYY-MM-DD format, return as is
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        return dateStr;
      }
      // Otherwise, try to parse and format
      try {
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
      } catch {
        return dateStr.split("T")[0]; // Fallback
      }
    };

    const submitData = {
      ...form,
      start_date: formatDateForAPI(form.start_date),
      end_date: formatDateForAPI(form.end_date),
    };

    try {
      if (editingId) {
        const res = await financialYearMasterApi.update(editingId, submitData);
        if (res.success) {
          toast({ title: "Financial year updated successfully" });
          setOpen(false);
          loadFinancialYears();
        }
      } else {
        const res = await financialYearMasterApi.create(submitData);
        if (res.success) {
          toast({ title: "Financial year created successfully" });
          setOpen(false);
          loadFinancialYears();
        }
      }
    } catch (e: any) {
      toast({
        title: editingId ? "Update failed" : "Create failed",
        description: e.message || `Unable to ${editingId ? "update" : "create"} financial year`,
        variant: "destructive",
      });
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  return (
    <Card className="border-0 shadow-md">
      <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-light">
              <Calendar className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle>Financial Year Master Data</CardTitle>
              <CardDescription>Manage valid financial year ranges for data uploads</CardDescription>
            </div>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button onClick={handleCreate} className="gap-2">
                <Plus className="h-4 w-4" />
                Add Financial Year
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>
                  {editingId ? "Edit Financial Year" : "Add Financial Year"}
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="financial_year">Financial Year *</Label>
                  <Input
                    id="financial_year"
                    value={form.financial_year}
                    onChange={(e) => setForm({ ...form, financial_year: e.target.value })}
                    placeholder="2024-25"
                  />
                  <p className="text-xs text-muted-foreground">Format: YYYY-YY (e.g., 2024-25)</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="start_date">Start Date *</Label>
                  <Input
                    id="start_date"
                    type="date"
                    value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_date">End Date *</Label>
                  <Input
                    id="end_date"
                    type="date"
                    value={form.end_date}
                    onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    placeholder="Optional description"
                  />
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/5 to-transparent border border-border/50">
                  <div className="space-y-0.5">
                    <Label>Active</Label>
                    <p className="text-sm text-muted-foreground">Allow data uploads for this financial year</p>
                  </div>
                  <Switch
                    checked={form.is_active}
                    onCheckedChange={(checked) => setForm({ ...form, is_active: checked })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSubmit}>
                  {editingId ? "Update" : "Create"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
            <p className="mt-2 text-muted-foreground">Loading financial years...</p>
          </div>
        ) : financialYears.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No financial years configured</p>
            <p className="text-sm mt-2">Click "Add Financial Year" to create one</p>
          </div>
        ) : (
          <div className="table-responsive">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Financial Year</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead>End Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {financialYears.map((fy) => (
                  <TableRow key={fy.id} className="hover:bg-muted/50">
                    <TableCell className="font-medium">
                      <Badge variant="outline">{fy.financial_year}</Badge>
                    </TableCell>
                    <TableCell>{formatDate(fy.start_date)}</TableCell>
                    <TableCell>{formatDate(fy.end_date)}</TableCell>
                    <TableCell>
                      <Badge variant={fy.is_active ? "default" : "secondary"}>
                        {fy.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {fy.description || "-"}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(fy)}
                          className="h-8 w-8 p-0"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(fy.id)}
                          className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
