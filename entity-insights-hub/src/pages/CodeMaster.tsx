import { useEffect, useState, useRef, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Combobox } from "@/components/ui/combobox";
import { Plus, MoreVertical, Upload as UploadIcon, FileSpreadsheet, Download, Edit, Trash2, Trash } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { codeMasterApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

type CodeMaster = {
  code_id: number;
  RawParticulars: string;
  mainCategory: string;
  category1?: string;
  category2?: string;
  category3?: string;
  category4?: string;
  category5?: string;
};

export default function CodeMasterPage() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [codes, setCodes] = useState<CodeMaster[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteAllDialogOpen, setDeleteAllDialogOpen] = useState(false);
  const [isDeletingAll, setIsDeletingAll] = useState(false);
  const [selectedCode, setSelectedCode] = useState<CodeMaster | null>(null);
  const [form, setForm] = useState({
    RawParticulars: "",
    mainCategory: "",
    category1: "",
    category2: "",
    category3: "",
    category4: "",
    category5: "",
  });
  const [uniqueValues, setUniqueValues] = useState<{
    mainCategory: string[];
    category1: string[];
    category2: string[];
    category3: string[];
    category4: string[];
    category5: string[];
  }>({
    mainCategory: [],
    category1: [],
    category2: [],
    category3: [],
    category4: [],
    category5: [],
  });
  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [operationId, setOperationId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "processing" | "completed" | "failed">("idle");
  const [progressMessage, setProgressMessage] = useState<string>("");
  const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [sortConfig, setSortConfig] = useState<{ key: keyof CodeMaster | null; direction: "asc" | "desc" }>({
    key: null,
    direction: "asc",
  });

  const loadCodes = async () => {
    try {
      setIsLoading(true);
      const res = await codeMasterApi.list();
      if (res.success && res.data?.codes) {
        // Sort by code_id DESC to show latest entries first
        const sortedCodes = [...(res.data.codes || [])].sort((a, b) => {
          return (b.code_id || 0) - (a.code_id || 0);
        });
        setCodes(sortedCodes);
      }
    } catch (e: any) {
      toast({ title: "Failed to load code master", description: e.message, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCodes();
    fetchUniqueValues();
  }, []);

  const fetchUniqueValues = async () => {
    try {
      const fields = ['mainCategory', 'category1', 'category2', 'category3', 'category4', 'category5'];
      const values: any = {};
      
      await Promise.all(
        fields.map(async (field) => {
          try {
            console.log(`📊 Fetching unique values for field: ${field}`);
            const res = await codeMasterApi.getUniqueValues(field);
            console.log(`✅ Response for ${field}:`, res);
            if (res.success && res.data) {
              values[field] = res.data.values || [];
              console.log(`   Found ${values[field].length} values:`, values[field]);
            } else {
              values[field] = [];
              console.log(`   No values found for ${field}`);
            }
          } catch (error) {
            console.error(`❌ Error fetching unique values for ${field}:`, error);
            values[field] = [];
          }
        })
      );
      
      console.log("📊 All unique values loaded:", values);
      setUniqueValues(values);
    } catch (error: any) {
      console.error("❌ Error fetching unique values:", error);
    }
  };

  const onCreate = async () => {
    try {
      if (!form.RawParticulars || !form.mainCategory) {
        toast({ title: "Missing fields", description: "RawParticulars and mainCategory are required", variant: "destructive" });
        return;
      }
      const res = await codeMasterApi.create({
        RawParticulars: form.RawParticulars,
        mainCategory: form.mainCategory,
        category1: form.category1 || undefined,
        category2: form.category2 || undefined,
        category3: form.category3 || undefined,
        category4: form.category4 || undefined,
        category5: form.category5 || undefined,
      });
      if (res.success) {
        toast({ title: "Code added" });
        setOpen(false);
        setForm({ RawParticulars: "", mainCategory: "", category1: "", category2: "", category3: "", category4: "", category5: "" });
        loadCodes();
        // Refresh unique values after adding new code
        fetchUniqueValues();
      }
    } catch (e: any) {
      toast({ title: "Create failed", description: e.message, variant: "destructive" });
    }
  };

  const handleEdit = (code: CodeMaster) => {
    setSelectedCode(code);
    setForm({
      RawParticulars: code.RawParticulars || "",
      mainCategory: code.mainCategory || "",
      category1: code.category1 || "",
      category2: code.category2 || "",
      category3: code.category3 || "",
      category4: code.category4 || "",
      category5: code.category5 || "",
    });
    setEditOpen(true);
  };

  const onUpdate = async () => {
    if (!selectedCode) return;
    try {
      if (!form.RawParticulars || !form.mainCategory) {
        toast({ title: "Missing fields", description: "RawParticulars and mainCategory are required", variant: "destructive" });
        return;
      }
      const res = await codeMasterApi.update(selectedCode.code_id, {
        RawParticulars: form.RawParticulars,
        mainCategory: form.mainCategory,
        category1: form.category1 || undefined,
        category2: form.category2 || undefined,
        category3: form.category3 || undefined,
        category4: form.category4 || undefined,
        category5: form.category5 || undefined,
      });
      if (res.success) {
        toast({ title: "Code updated" });
        setEditOpen(false);
        setSelectedCode(null);
        setForm({ RawParticulars: "", mainCategory: "", category1: "", category2: "", category3: "", category4: "", category5: "" });
        loadCodes();
        // Refresh unique values after updating code
        fetchUniqueValues();
      }
    } catch (e: any) {
      toast({ title: "Update failed", description: e.message, variant: "destructive" });
    }
  };

  const handleDelete = (code: CodeMaster) => {
    setSelectedCode(code);
    setDeleteDialogOpen(true);
  };

  const onDelete = async () => {
    if (!selectedCode) return;
    try {
      const res = await codeMasterApi.delete(selectedCode.code_id);
      if (res.success) {
        toast({ title: "Code deleted" });
        setDeleteDialogOpen(false);
        setSelectedCode(null);
        loadCodes();
        // Refresh unique values after deleting code
        fetchUniqueValues();
      }
    } catch (e: any) {
      toast({ title: "Delete failed", description: e.message, variant: "destructive" });
    }
  };

  const onDeleteAll = async () => {
    if (isDeletingAll) return;
    try {
      setIsDeletingAll(true);
      const res = await codeMasterApi.deleteAll();
      if (res.success) {
        toast({
          title: "All codes deleted",
          description: `${res.data?.deleted_count ?? 0} record(s) removed`,
        });
        setCodes([]);
        setDeleteAllDialogOpen(false);
        // reload to be safe in case backend returns updated list/state
        loadCodes();
        fetchUniqueValues();
      } else {
        toast({
          title: "Delete all failed",
          description: res.message || "Unable to delete all codes",
          variant: "destructive",
        });
      }
    } catch (e: any) {
      toast({ title: "Delete all failed", description: e.message, variant: "destructive" });
    } finally {
      setIsDeletingAll(false);
    }
  };

  const handleSort = (column: keyof CodeMaster) => {
    setSortConfig((current) => {
      if (current.key === column) {
        return {
          key: column,
          direction: current.direction === "asc" ? "desc" : "asc",
        };
      }
      return { key: column, direction: "asc" };
    });
  };

  const sortedCodes = useMemo(() => {
    if (!sortConfig.key) return codes;
    const key = sortConfig.key;
    const direction = sortConfig.direction;

    return [...codes].sort((a, b) => {
      const aVal = (a[key] ?? "").toString().toLowerCase();
      const bVal = (b[key] ?? "").toString().toLowerCase();

      if (aVal < bVal) return direction === "asc" ? -1 : 1;
      if (aVal > bVal) return direction === "asc" ? 1 : -1;
      return 0;
    });
  }, [codes, sortConfig]);

  // Upload handlers
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const validExtensions = ['.xlsx', '.xls', '.csv'];
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      
      if (!validExtensions.includes(fileExtension)) {
        toast({
          title: "Invalid File",
          description: "Please select an Excel file (.xlsx, .xls, or .csv)",
          variant: "destructive",
        });
        return;
      }
      
      setSelectedFile(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const validExtensions = ['.xlsx', '.xls', '.csv'];
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      
      if (!validExtensions.includes(fileExtension)) {
        toast({
          title: "Invalid File",
          description: "Please select an Excel file (.xlsx, .xls, or .csv)",
          variant: "destructive",
        });
        return;
      }
      
      setSelectedFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast({
        title: "No File Selected",
        description: "Please select a file to upload",
        variant: "destructive",
      });
      return;
    }

    try {
      const opId =
        typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : `op-${Date.now()}`;

      setOperationId(opId);
      setUploadProgress(0);
      setUploadStatus("uploading");
      setProgressMessage("Uploading file...");
      startProgressPolling(opId);

      setIsUploading(true);
      const response = await codeMasterApi.uploadFile(selectedFile, opId);

      if (response.success) {
        const data = response.data;
        const recordsInserted = data?.records_inserted || 0;
        const recordsUpdated = data?.records_updated || 0;
        const totalRows = data?.total_rows || 0;
        setUploadProgress(100);
        setUploadStatus("completed");
        setProgressMessage("Processing complete");
        
        toast({
          title: "Upload Successful! 🎉",
          description: `Processed ${totalRows} rows. ${recordsInserted} records inserted, ${recordsUpdated} records updated.`,
        });
        
        // Show warnings if any
        if (response.warnings && response.warnings.length > 0) {
          setTimeout(() => {
            toast({
              title: "Processing Warnings",
              description: `${response.warnings.length} rows had issues. Check console for details.`,
              variant: "destructive",
            });
          }, 1000);
        }
        
        // Reset form and reload codes
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        loadCodes();
        fetchUniqueValues();
        
        // Close dialog after successful upload
        setTimeout(() => {
          setUploadDialogOpen(false);
        }, 2000);
      }
    } catch (error: any) {
      console.error("Upload error:", error);
      setUploadStatus("failed");
      setProgressMessage(error.message || "Upload failed");
      toast({
        title: "Upload Failed",
        description: error.message || "Failed to upload file. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
      clearProgressInterval();
    }
  };

  const startProgressPolling = (opId: string) => {
    clearProgressInterval();
    progressIntervalRef.current = setInterval(async () => {
      try {
        const res = await codeMasterApi.getUploadProgress(opId);
        if (res.success && res.data) {
          const { progress, message, status } = res.data as any;
          setUploadProgress(progress || 0);
          if (message) setProgressMessage(message);
          if (status === "completed") {
            setUploadStatus("completed");
            clearProgressInterval();
          } else if (status === "failed") {
            setUploadStatus("failed");
            clearProgressInterval();
          } else {
            setUploadStatus("processing");
          }
        }
      } catch (pollErr) {
        console.error("Progress polling error:", pollErr);
      }
    }, 1500);
  };

  const clearProgressInterval = () => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      clearProgressInterval();
    };
  }, []);

  const handleDownloadTemplate = () => {
    try {
      const link = document.createElement('a');
      link.href = '/assets/codeMasterTemplate.xlsx';
      link.download = 'codeMasterTemplate.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast({
        title: "Template Downloaded",
        description: "Template file downloaded successfully",
      });
    } catch (error: any) {
      toast({
        title: "Download Failed",
        description: error.message || "Failed to download template",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="page-shell">
      <div className="space-y-1 mb-6">
        <h1 className="page-title text-3xl sm:text-4xl">Code Master</h1>
        <p className="subtle-text">Manage standardized codes and categories</p>
      </div>

      <div className="toolbar-stack mb-6">
        <div>
          <h2 className="text-xl font-semibold">Code Management</h2>
        </div>
        <div className="flex gap-2">
          <Button
            variant="destructive"
            onClick={() => setDeleteAllDialogOpen(true)}
            className="gap-2"
            disabled={codes.length === 0}
          >
            <Trash className="h-4 w-4" />
            Delete All
          </Button>
          <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 gradient-primary text-white shadow-primary">
                <UploadIcon className="h-4 w-4" />
                Upload File
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <UploadIcon className="h-5 w-5" />
                  Upload Code Master File
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-6 py-4">
                <div className="flex justify-end">
                  <Button
                    variant="outline"
                    onClick={handleDownloadTemplate}
                    className="gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Download Template
                  </Button>
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                <div
                  className="border-2 border-dashed border-primary/30 rounded-lg p-12 text-center hover:border-primary hover:bg-primary/5 transition-all cursor-pointer group"
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="flex flex-col items-center gap-3">
                    <div className="p-4 rounded-full bg-primary-light group-hover:bg-primary/20 transition-colors">
                      <FileSpreadsheet className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                      {selectedFile ? (
                        <>
                          <p className="text-lg font-medium">{selectedFile.name}</p>
                          <p className="text-sm text-muted-foreground">Click to change file</p>
                        </>
                      ) : (
                        <>
                          <p className="text-lg font-medium">Drop your Excel file here</p>
                          <p className="text-sm text-muted-foreground">or click to browse</p>
                          <p className="text-xs text-muted-foreground mt-2">
                            Required columns: RawParticulars, mainCategory<br />
                            Optional columns: category1, category2, category3, category4, category5
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {(uploadStatus !== "idle" || isUploading) && (
                  <div className="space-y-2 rounded-lg border border-dashed border-primary/30 p-4 bg-primary/5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-primary">
                        {progressMessage || "Processing..."}
                      </span>
                      <span className="text-muted-foreground">{uploadProgress}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-muted">
                      <div
                        className="h-2 rounded-full bg-primary transition-all"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Status: {uploadStatus === "uploading" ? "Uploading file" : uploadStatus}
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setUploadDialogOpen(false);
                      setSelectedFile(null);
                      setUploadStatus("idle");
                      setUploadProgress(0);
                      if (fileInputRef.current) {
                        fileInputRef.current.value = "";
                      }
                    }}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    className="flex-1 gradient-primary text-white shadow-primary"
                    onClick={handleUpload}
                    disabled={isUploading || !selectedFile}
                  >
                    {isUploading ? "Uploading..." : "Upload & Process File"}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 gradient-primary text-white shadow-primary">
              <Plus className="h-4 w-4" />
              Add Code
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Add Code</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
              <div className="space-y-2 md:col-span-2">
                <Label>Raw Particulars</Label>
                <Input value={form.RawParticulars} onChange={(e) => setForm({ ...form, RawParticulars: e.target.value })} placeholder="Bank Charges" />
              </div>
              <div className="space-y-2">
                <Label>Main Category</Label>
                <Combobox
                  value={form.mainCategory}
                  onValueChange={(value) => setForm({ ...form, mainCategory: value })}
                  options={uniqueValues.mainCategory}
                  placeholder="Type or select main category..."
                  searchPlaceholder="Search main categories..."
                  emptyMessage="No main categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 1</Label>
                <Combobox
                  value={form.category1}
                  onValueChange={(value) => setForm({ ...form, category1: value })}
                  options={uniqueValues.category1}
                  placeholder="Type or select category 1..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 2</Label>
                <Combobox
                  value={form.category2}
                  onValueChange={(value) => setForm({ ...form, category2: value })}
                  options={uniqueValues.category2}
                  placeholder="Type or select category 2..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 3</Label>
                <Combobox
                  value={form.category3}
                  onValueChange={(value) => setForm({ ...form, category3: value })}
                  options={uniqueValues.category3}
                  placeholder="Type or select category 3..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 4</Label>
                <Combobox
                  value={form.category4}
                  onValueChange={(value) => setForm({ ...form, category4: value })}
                  options={uniqueValues.category4}
                  placeholder="Type or select category 4..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 5</Label>
                <Combobox
                  value={form.category5}
                  onValueChange={(value) => setForm({ ...form, category5: value })}
                  options={uniqueValues.category5}
                  placeholder="Type or select category 5..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button className="gradient-primary text-white" onClick={onCreate}>Save</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={editOpen} onOpenChange={setEditOpen}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Edit Code</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
              <div className="space-y-2 md:col-span-2">
                <Label>Raw Particulars</Label>
                <Input value={form.RawParticulars} onChange={(e) => setForm({ ...form, RawParticulars: e.target.value })} placeholder="Bank Charges" />
              </div>
              <div className="space-y-2">
                <Label>Main Category</Label>
                <Combobox
                  value={form.mainCategory}
                  onValueChange={(value) => setForm({ ...form, mainCategory: value })}
                  options={uniqueValues.mainCategory}
                  placeholder="Type or select main category..."
                  searchPlaceholder="Search main categories..."
                  emptyMessage="No main categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 1</Label>
                <Combobox
                  value={form.category1}
                  onValueChange={(value) => setForm({ ...form, category1: value })}
                  options={uniqueValues.category1}
                  placeholder="Type or select category 1..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 2</Label>
                <Combobox
                  value={form.category2}
                  onValueChange={(value) => setForm({ ...form, category2: value })}
                  options={uniqueValues.category2}
                  placeholder="Type or select category 2..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 3</Label>
                <Combobox
                  value={form.category3}
                  onValueChange={(value) => setForm({ ...form, category3: value })}
                  options={uniqueValues.category3}
                  placeholder="Type or select category 3..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 4</Label>
                <Combobox
                  value={form.category4}
                  onValueChange={(value) => setForm({ ...form, category4: value })}
                  options={uniqueValues.category4}
                  placeholder="Type or select category 4..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
              <div className="space-y-2">
                <Label>Category 5</Label>
                <Combobox
                  value={form.category5}
                  onValueChange={(value) => setForm({ ...form, category5: value })}
                  options={uniqueValues.category5}
                  placeholder="Type or select category 5..."
                  searchPlaceholder="Search categories..."
                  emptyMessage="No categories found. Type to create new."
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setEditOpen(false);
                setSelectedCode(null);
                setForm({ RawParticulars: "", mainCategory: "", category1: "", category2: "", category3: "", category4: "", category5: "" });
              }}>Cancel</Button>
              <Button className="gradient-primary text-white" onClick={onUpdate}>Update</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the code master entry for
                <strong> "{selectedCode?.RawParticulars}"</strong>.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => {
                setDeleteDialogOpen(false);
                setSelectedCode(null);
              }}>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={onDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <AlertDialog open={deleteAllDialogOpen} onOpenChange={setDeleteAllDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete All Codes?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete <strong>all {codes.length} record(s)</strong> from the code master table.
                <br /><br />
                This is a destructive operation that will remove all code master entries.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setDeleteAllDialogOpen(false)}>Cancel</AlertDialogCancel>
              <AlertDialogAction 
                onClick={onDeleteAll} 
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                disabled={isDeletingAll}
              >
                {isDeletingAll ? "Deleting..." : "Delete All"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
        </div>
      </div>

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
          <CardTitle>All Codes</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="table-responsive">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort("RawParticulars")}
                >
                  Raw Particulars
                </TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort("mainCategory")}
                >
                  Main Category
                </TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort("category1")}
                >
                  Category 1
                </TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort("category2")}
                >
                  Category 2
                </TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort("category3")}
                >
                  Category 3
                </TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort("category4")}
                >
                  Category 4
                </TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort("category5")}
                >
                  Category 5
                </TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedCodes.map((c) => (
                <TableRow key={c.code_id} className="hover:bg-muted/50">
                  <TableCell className="font-medium">{c.RawParticulars}</TableCell>
                  <TableCell className="text-primary">{c.mainCategory}</TableCell>
                  <TableCell>{c.category1 || "—"}</TableCell>
                  <TableCell>{c.category2 || "—"}</TableCell>
                  <TableCell>{c.category3 || "—"}</TableCell>
                  <TableCell>{c.category4 || "—"}</TableCell>
                  <TableCell>{c.category5 || "—"}</TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEdit(c)}>
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleDelete(c)} className="text-destructive">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
              {(!codes || codes.length === 0) && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                    {isLoading ? "Loading..." : "No codes found"}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}




