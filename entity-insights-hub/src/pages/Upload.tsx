import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Upload as UploadIcon, FileSpreadsheet, CheckCircle, XCircle, Clock } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect, useRef } from "react";
import { uploadApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface Entity {
  ent_id: number;
  ent_name: string;
  ent_code: string;
  lcl_curr?: string;
  city?: string;
  country?: string;
}

interface Month {
  mnt_id: number;
  month_short: string;
  month_name: string;
  year: number;
  qtr?: string;
  half?: string;
}

export default function Upload() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [months, setMonths] = useState<Month[]>([]);
  const [financialYears, setFinancialYears] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [operationId, setOperationId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "processing" | "completed" | "failed">("idle");
  const [progressMessage, setProgressMessage] = useState<string>("");
  const [formData, setFormData] = useState({
    ent_id: "",
    month_name: "",
    financial_year: "",
  });
  const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [showNewCompanyDialog, setShowNewCompanyDialog] = useState(false);
  const [newCompany, setNewCompany] = useState<number | null>(null);

  const fiscalMonthOrder = [
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "January",
    "February",
    "March",
  ];

  const normalizeMonthName = (name: string) => {
    const lower = (name || "").trim().toLowerCase();
    const mapping: Record<string, string> = {
      jan: "january",
      "jan.": "january",
      january: "january",
      feb: "february",
      "feb.": "february",
      february: "february",
      mar: "march",
      "mar.": "march",
      march: "march",
      apr: "april",
      "apr.": "april",
      april: "april",
      may: "may",
      jun: "june",
      "jun.": "june",
      june: "june",
      jul: "july",
      "jul.": "july",
      july: "july",
      aug: "august",
      "aug.": "august",
      august: "august",
      sep: "september",
      sept: "september",
      "sep.": "september",
      "sept.": "september",
      september: "september",
      oct: "october",
      "oct.": "october",
      october: "october",
      nov: "november",
      "nov.": "november",
      november: "november",
      dec: "december",
      "dec.": "december",
      december: "december",
    };

    return mapping[lower] || name;
  };

  const getMonthDisplayName = (name: string) => {
    const normalized = normalizeMonthName(name);
    if (!normalized) return name;
    return normalized.charAt(0).toUpperCase() + normalized.slice(1);
  };

  const getFiscalMonthOrderIndex = (name: string) => {
    const normalized = normalizeMonthName(name).toLowerCase();
    const idx = fiscalMonthOrder.findIndex(
      (month) => month.toLowerCase() === normalized
    );
    return idx === -1 ? Number.MAX_SAFE_INTEGER : idx;
  };

  // Fetch entities and months on component mount
  useEffect(() => {
    fetchEntities();
    fetchMonths();
    fetchFinancialYears();
  }, []);

  const fetchEntities = async () => {
    try {
      setIsLoading(true);
      const response = await uploadApi.getEntities();
      if (response.success && response.data) {
        setEntities(response.data.entities);
      }
    } catch (error: any) {
      console.error("Error fetching entities:", error);
      toast({
        title: "Error",
        description: "Failed to load entities. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMonths = async () => {
    try {
      const response = await uploadApi.getMonths();
      if (response.success && response.data) {
        setMonths(response.data.months);
      }
    } catch (error: any) {
      console.error("Error fetching months:", error);
      toast({
        title: "Error",
        description: "Failed to load months. Please try again.",
        variant: "destructive",
      });
    }
  };

  const fetchFinancialYears = async () => {
    try {
      const response = await uploadApi.getFinancialYears();
      if (response.success && response.data) {
        setFinancialYears(response.data.years);
      }
    } catch (error: any) {
      console.error("Error fetching financial years:", error);
      toast({
        title: "Error",
        description: "Failed to load financial years. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check if file is Excel
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

    if (!formData.ent_id || !formData.month_name || !formData.financial_year) {
      toast({
        title: "Missing Information",
        description: "Please select Entity, Month, and Financial Year",
        variant: "destructive",
      });
      return;
    }

    // Show dialog to ask about starting month balance sheet
    setShowNewCompanyDialog(true);
  };

  const handleNewCompanyDialogResponse = async (isNewCompany: boolean) => {
    setShowNewCompanyDialog(false);
    setNewCompany(isNewCompany ? 1 : 0);
    
    // Proceed with upload after dialog response
    await proceedWithUpload(isNewCompany ? 1 : 0);
  };

  const proceedWithUpload = async (newCompanyValue: number) => {
    if (!selectedFile) {
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
      const response = await uploadApi.uploadFile(
        selectedFile,
        formData.ent_id,
        formData.month_name,
        formData.financial_year,
        opId,
        newCompanyValue
      );

      if (response.success) {
        const data = response.data;
        const recordsInserted = data?.records_inserted || 0;
        const totalRows = data?.total_rows || 0;
        setUploadProgress(100);
        setUploadStatus("completed");
        setProgressMessage("Processing complete");
        
        toast({
          title: "Upload Successful! 🎉",
          description: `Processed ${totalRows} rows. ${recordsInserted} records inserted into database.`,
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
        
        // Reset form
        setSelectedFile(null);
        setNewCompany(null);
        setFormData({
          ent_id: "",
          month_name: "",
          financial_year: "",
        });
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
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
        const res = await uploadApi.getUploadProgress(opId);
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

  // Static list of all 12 months in fiscal order (April to March)
  const allMonths = fiscalMonthOrder;

  // Calculate the correct year for a month in the fiscal year
  // Financial year 2024 means FY 2024-25 (starting April 2024, ending March 2025)
  // So April-December use the starting year (financial_year), January-March use the next year (financial_year + 1)
  const getYearForMonth = (monthName: string, financialYear: string): string => {
    if (!financialYear) return "";
    const fy = parseInt(financialYear, 10);
    if (isNaN(fy)) return financialYear;
    
    const normalizedMonth = normalizeMonthName(monthName).toLowerCase();
    // Months from January to March (last 3 in fiscal order) are in the next calendar year
    const nextYearMonths = ['january', 'february', 'march'];
    
    if (nextYearMonths.includes(normalizedMonth)) {
      return (fy + 1).toString();
    }
    // April to December use the same year
    return fy.toString();
  };

  return (
    <div className="page-shell">
      <div className="space-y-1">
        <h1 className="page-title text-3xl sm:text-4xl">Upload Financial Data</h1>
        <p className="subtle-text">Upload Excel files and preview the data</p>
      </div>

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary-light"><UploadIcon className="h-5 w-5 text-primary" /></div>
            Upload New File
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Select Entity</Label>
              <Select
                value={formData.ent_id}
                onValueChange={(value) => setFormData({ ...formData, ent_id: value })}
                disabled={isLoading || isUploading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose entity" />
                </SelectTrigger>
                <SelectContent>
                  {entities.map((entity) => (
                    <SelectItem key={entity.ent_id} value={entity.ent_id.toString()}>
                      {entity.ent_name} ({entity.ent_code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Financial Year</Label>
              <Input
                type="number"
                placeholder="Enter year (e.g., 2024)"
                value={formData.financial_year}
                onChange={(e) => {
                  setFormData({ ...formData, financial_year: e.target.value, month_name: "" });
                }}
                disabled={isLoading || isUploading}
                min="2000"
                max="2100"
              />
            </div>
            <div className="space-y-2">
              <Label>Month</Label>
              <Select
                value={formData.month_name}
                onValueChange={(value) => setFormData({ ...formData, month_name: value })}
                disabled={isLoading || isUploading || !formData.financial_year}
              >
                <SelectTrigger>
                  <SelectValue placeholder={formData.financial_year ? "Select month" : "Select financial year first"} />
                </SelectTrigger>
                <SelectContent className="max-h-[300px]">
                  {allMonths.map((monthName) => {
                    const yearForMonth = getYearForMonth(monthName, formData.financial_year);
                    return (
                      <SelectItem key={monthName} value={monthName}>
                        {monthName} {yearForMonth}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
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

          <Button
            className="w-full gradient-primary text-white shadow-primary"
            onClick={handleUpload}
            disabled={isUploading || !selectedFile || !formData.ent_id || !formData.month_name || !formData.financial_year}
          >
            {isUploading ? "Uploading..." : "Upload & Process File"}
          </Button>
        </CardContent>
      </Card>

      {/* New Company Dialog */}
      <AlertDialog open={showNewCompanyDialog} onOpenChange={(open) => {
        if (!open && showNewCompanyDialog) {
          // If dialog is closed without selecting (e.g., clicking outside), default to "No"
          handleNewCompanyDialogResponse(false);
        }
      }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Starting Month Balance Sheet</AlertDialogTitle>
            <AlertDialogDescription>
              Is this your company's starting month balance sheet?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => handleNewCompanyDialogResponse(false)}>
              No
            </AlertDialogCancel>
            <AlertDialogAction onClick={() => handleNewCompanyDialogResponse(true)}>
              Yes
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
