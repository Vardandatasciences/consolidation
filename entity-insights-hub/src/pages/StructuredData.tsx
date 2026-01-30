import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, TrendingUp, AlertTriangle, Plus, Download, Trash } from "lucide-react";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Combobox } from "@/components/ui/combobox";
import { useState, useEffect, useMemo } from "react";
import { structuredDataApi, uploadApi, codeMasterApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { X } from "lucide-react";

interface Entity {
  ent_id: number;
  ent_name: string;
  ent_code: string;
}

interface StructuredDataRecord {
  // Common fields (optional), plus allow any extra columns from DB
  category?: string;
  sub_category?: string;
  account_name?: string;
  code?: string;
  amount?: string | number;
  entity_id?: number | string;
  financial_year?: number | string;
  [key: string]: unknown;
}

export default function StructuredData() {
  const { toast } = useToast();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [financialYears, setFinancialYears] = useState<number[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<string>("all");
  const [selectedYear, setSelectedYear] = useState<string>("all");
  const [mainCategoryFilter, setMainCategoryFilter] = useState<"all" | "missing" | "available">("all");
  const [balanceSheetData, setBalanceSheetData] = useState<StructuredDataRecord[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [totalAssets, setTotalAssets] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [columnFilters, setColumnFilters] = useState<Record<string, string>>({});
  const [draggingCol, setDraggingCol] = useState<string | null>(null);
  const [hoveredRowIndex, setHoveredRowIndex] = useState<number | null>(null);
  const [addDataDialogOpen, setAddDataDialogOpen] = useState(false);
  const [selectedRowForAdd, setSelectedRowForAdd] = useState<{row: StructuredDataRecord, index: number} | null>(null);
  const [codeForm, setCodeForm] = useState({
    RawParticulars: "",
    mainCategory: "",
    category1: "",
    category2: "",
    category3: "",
    category4: "",
    category5: "",
  });
  const [isSavingCode, setIsSavingCode] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
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
  const [loadingUniqueValues, setLoadingUniqueValues] = useState(false);
  const [deleteAllDialogOpen, setDeleteAllDialogOpen] = useState(false);
  const [isDeletingAll, setIsDeletingAll] = useState(false);

  // Fetch entities and financial years on component mount
  useEffect(() => {
    fetchEntities();
    fetchFinancialYears();
  }, []);

  // Fetch structured data when filters change
  useEffect(() => {
    fetchStructuredData();
  }, [selectedEntity, selectedYear]);

  // Fetch unique values for autocomplete
  useEffect(() => {
    fetchUniqueValues();
  }, []);

  const fetchUniqueValues = async () => {
    try {
      setLoadingUniqueValues(true);
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
    } finally {
      setLoadingUniqueValues(false);
    }
  };

  const fetchEntities = async () => {
    try {
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

  const fetchStructuredData = async () => {
    try {
      setIsLoading(true);
      // Parse entityId and financialYear, treating "all" as undefined (no filter)
      const entityId = selectedEntity && selectedEntity !== "all" ? parseInt(selectedEntity) : undefined;
      const financialYear = selectedYear && selectedYear !== "all" ? parseInt(selectedYear) : undefined;
      
      const response = await structuredDataApi.getData(entityId, financialYear);
      
      if (response.success && response.data) {
        setBalanceSheetData(response.data.records || []);
        setTotalAssets(response.data.total_assets || 0);
        const records: StructuredDataRecord[] = response.data.records || [];
        
        // Debug: Log sample data to check if Avg_Fx_Rt and transactionAmountUSD are present
        if (records.length > 0) {
          const sample = records[0];
          console.log("🔍 Sample record from API:", {
            particular: sample.Particular || sample.particular,
            mainCategory: sample.mainCategory || sample.maincategory,
            category1: sample.category1 || sample.Category1,
            localCurrencyCode: sample.localCurrencyCode || sample.localcurrencycode,
            Avg_Fx_Rt: sample.Avg_Fx_Rt || sample.avg_fx_rt,
            transactionAmountUSD: sample.transactionAmountUSD || sample.transactionamountusd,
            allKeys: Object.keys(sample)
          });
        }
        const allKeys = new Set<string>();
        records.forEach((row) => Object.keys(row || {}).forEach((k) => allKeys.add(k)));
        // Exclude UI alias columns and unwanted columns
        const exclude = new Set([
          "category", 
          "sub_category", 
          "account_name", 
          "code", 
          "amount",
          "ent_code",      // Ent Code - remove
          "entitycode",    // Entity Code - remove
          "half",          // Half - remove
          "qtr",           // Qtr - remove
        ]);
        
        // Define the desired column order (case-insensitive matching)
        // Only show the requested columns in this sequence
        const desiredOrder = [
          "particular",
          "entityname",
          "localcurrencycode",
          "maincategory",
          "category1",
          "category2",
          "category3",
          "category4",
          "category5",
          "month",
          "year",
          "transactionamount",
          "avg_fx_rt",
          "transactionamountusd",
        ];
        
        // Helper function to find matching key (case-insensitive)
        const findMatchingKey = (desiredKey: string, availableKeys: Set<string>): string | null => {
          const lowerDesired = desiredKey.toLowerCase();
          for (const key of availableKeys) {
            if (key.toLowerCase() === lowerDesired) {
              return key;
            }
          }
          return null;
        };
        
        // Build ordered columns based on desired order
        const orderedColumns: string[] = [];
        const usedKeys = new Set<string>();
        
        // First, add columns in the desired order
        desiredOrder.forEach((desiredKey) => {
          const matchingKey = findMatchingKey(desiredKey, allKeys);
          if (matchingKey) {
            // Check if excluded (case-insensitive)
            const lowerKey = matchingKey.toLowerCase();
            const isExcluded = Array.from(exclude).some(ex => lowerKey === ex.toLowerCase());
            if (!isExcluded) {
              orderedColumns.push(matchingKey);
              usedKeys.add(matchingKey);
            }
          }
        });
        
        setColumns(orderedColumns);
      }
    } catch (error: any) {
      console.error("Error fetching structured data:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to load structured data. Please try again.",
        variant: "destructive",
      });
      setBalanceSheetData([]);
      setTotalAssets(0);
    } finally {
      setIsLoading(false);
    }
  };

  // Format currency amount
  const formatAmount = (amount: string | number): string => {
    if (typeof amount === 'string') {
      // If already formatted, return as is
      if (amount.includes('₹')) {
        return amount;
      }
      // Otherwise parse and format
      const numAmount = parseFloat(amount.replace(/,/g, '')) || 0;
      return `₹${numAmount.toLocaleString('en-IN')}`;
    }
    return `₹${amount.toLocaleString('en-IN')}`;
  };

  // Format total assets for display
  const formatTotalAssets = (amount: number): string => {
    if (amount >= 10000000) {
      // Convert to Crores
      const crores = amount / 10000000;
      return `₹${crores.toFixed(2)} Cr`;
    } else if (amount >= 100000) {
      // Convert to Lakhs
      const lakhs = amount / 100000;
      return `₹${lakhs.toFixed(2)} L`;
    }
    return formatAmount(amount);
  };

  const humanizeColumnName = (key: string): string => {
    const lowerKey = key.toLowerCase();
    const specialCases: Record<string, string> = {
      category1: "Category 1",
      category2: "Category 2",
      category3: "Category 3",
      category4: "Category 4",
      category5: "Category 5",
    };

    if (specialCases[lowerKey]) {
      return specialCases[lowerKey];
    }

    // Handle camelCase conversion
    const camelCaseConverted = key.replace(/([A-Z])/g, ' $1').trim();
    // Replace underscores and capitalize
    return camelCaseConverted.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const isNumericValue = (value: unknown): boolean => {
    if (typeof value === "number") return true;
    if (typeof value === "string") {
      const cleaned = value.replace(/,/g, "").trim();
      return cleaned !== "" && !isNaN(Number(cleaned));
    }
    return false;
  };

  const renderCellValue = (key: string, value: unknown): string => {
    // Format amount-like fields (e.g., transactionAmount, transactionAmountUSD, amount*)
    if (/(^|_)(transactionamount|amt|amount)(_|$)/i.test(key)) {
      if (typeof value === "number" || typeof value === "string") {
        return formatAmount(value as any);
      }
    }
    // Format forex rate fields
    if (/avg_fx_rt|avrg.*forex|forex.*rate/i.test(key)) {
      if (typeof value === "number" || typeof value === "string") {
        const numValue = typeof value === "string" ? parseFloat(value) : value;
        if (!isNaN(numValue)) {
          return numValue.toFixed(4);
        }
      }
    }
    if (value === null || value === undefined) return "";
    return String(value);
  };

  // Filter data based on column filters
  const filteredData = useMemo(() => {
    if (!balanceSheetData || balanceSheetData.length === 0) return [];
    
    // Helper: check mainCategory presence (supports both mainCategory / maincategory keys)
    const hasMainCategory = (row: StructuredDataRecord) => {
      const r: any = row;
      const val = r.mainCategory ?? r.maincategory ?? r.code ?? "";
      return typeof val === "string"
        ? val.trim() !== ""
        : val !== null && val !== undefined;
    };

    return balanceSheetData.filter((row) => {
      // 1) Apply mainCategory availability filter
      if (mainCategoryFilter === "missing" && hasMainCategory(row)) {
        return false;
      }
      if (mainCategoryFilter === "available" && !hasMainCategory(row)) {
        return false;
      }

      // 2) Apply per-column text filters
      if (Object.keys(columnFilters).length === 0) return true;

      return columns.every((col) => {
        const filterValue = columnFilters[col];
        if (!filterValue || filterValue.trim() === "") return true;

        const cellValue = (row as any)[col];
        if (cellValue === null || cellValue === undefined) return false;

        const cellStr = String(cellValue).toLowerCase();
        const filterStr = filterValue.toLowerCase().trim();

        return cellStr.includes(filterStr);
      });
    });
  }, [balanceSheetData, columnFilters, columns, mainCategoryFilter]);

  // Update column filter
  const updateColumnFilter = (column: string, value: string) => {
    setColumnFilters((prev) => ({
      ...prev,
      [column]: value,
    }));
  };

  // Clear all filters
  const clearAllFilters = () => {
    setColumnFilters({});
  };

  const reorderColumns = (source: string, target: string) => {
    if (!source || !target || source === target) return;
    setColumns((prev) => {
      const next = [...prev];
      const fromIdx = next.indexOf(source);
      const toIdx = next.indexOf(target);
      if (fromIdx === -1 || toIdx === -1) return prev;
      next.splice(fromIdx, 1);
      next.splice(toIdx, 0, source);
      return next;
    });
  };

  // Check if a cell value is missing (excluding avg_fx_rt and category5)
  const isMissingValue = (col: string, value: unknown): boolean => {
    // Skip avg_fx_rt and category5/categoty5 from highlighting
    if (/avg_fx_rt|category5|categoty5/i.test(col)) return false;

    return (
      value === null ||
      value === undefined ||
      value === '' ||
      (typeof value === 'string' && value.trim() === '')
    );
  };

  // Calculate missing data counts for each column (excluding avg_fx_rt and category5)
  const missingDataCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    if (!balanceSheetData || balanceSheetData.length === 0) return counts;

    balanceSheetData.forEach((row) => {
      columns.forEach((col) => {
        // Skip avg_fx_rt and category5/categoty5 from highlighting
        if (/avg_fx_rt|category5|categoty5/i.test(col)) return;

        const value = (row as any)[col];
        // Check if value is missing (null, undefined, empty string, or whitespace)
        const isEmpty = 
          value === null || 
          value === undefined || 
          value === '' || 
          (typeof value === 'string' && value.trim() === '');

        if (isEmpty) {
          counts[col] = (counts[col] || 0) + 1;
        }
      });
    });

    return counts;
  }, [balanceSheetData, columns]);

  const rowHasMissingData = (row: StructuredDataRecord, cols: string[]) => {
    return (cols.length > 0 ? cols : Object.keys(row || {})).some((col) => {
      if (/avg_fx_rt/i.test(col)) return false;
      const value = (row as any)[col];
      return isMissingValue(col, value);
    });
  };

  const missingRowsCount = useMemo(() => {
    if (!filteredData || filteredData.length === 0) return 0;
    return filteredData.filter((row) => rowHasMissingData(row, columns)).length;
  }, [filteredData, columns]);

  // Handle add data action for a row
  const handleAddData = async (rowIndex: number, row: StructuredDataRecord) => {
    // Get particular value from row (could be in different column names)
    const rawParticular =
      (row as any)?.particular ||
      (row as any)?.Particular ||
      (row as any)?.account_name ||
      "";
    const particular = typeof rawParticular === "string" ? rawParticular.trim() : String(rawParticular || "").trim();
    
    // Get category data from row (check both new column names and old names for backward compatibility)
    const rowData = row as any;
    // mainCategory
    const mainCat = rowData?.mainCategory || rowData?.maincategory || rowData?.standardizedCode || rowData?.standardizedcode || rowData?.Std_Code || rowData?.std_code || "";
    // category1
    const brdCls = rowData?.category1 || rowData?.Category1 || rowData?.Brd_Cls || rowData?.brd_cls || "";
    // category2
    const brdCls2 = rowData?.category2 || rowData?.Category2 || rowData?.Brd_Cls_2 || rowData?.brd_cls_2 || "";
    // category3
    const ctgCode = rowData?.category3 || rowData?.Category3 || rowData?.Ctg_code || rowData?.ctg_code || "";
    // category4
    const caFlFnFl = rowData?.category4 || rowData?.Category4 || rowData?.CaFl_FnFl || rowData?.cafl_fnfl || "";
    // category5
    const cat5 = rowData?.category5 || rowData?.Category5 || rowData?.Cat_5 || rowData?.cat_5 || "";
    
    console.log("📊 Row data for add dialog:", { 
      particular, 
      mainCat, 
      brdCls, 
      brdCls2, 
      ctgCode, 
      caFlFnFl, 
      cat5,
      rawRow: row 
    });
    
    // Initialize form with particular and row data
    let formData = {
      RawParticulars: String(particular || ""),
      mainCategory: String(mainCat || ""),
      category1: String(brdCls || ""),
      category2: String(brdCls2 || ""),
      category3: String(ctgCode || ""),
      category4: String(caFlFnFl || ""),
      category5: String(cat5 || ""),
    };
    
    // Try to find existing code master entry for this particular
    // This will override row data if a code master entry exists
    if (particular) {
      try {
        const codeRes = await codeMasterApi.getByParticular(particular);
        if (codeRes.success && codeRes.data) {
          // Pre-fill all fields from existing code master entry (takes priority)
          formData = {
            RawParticulars: codeRes.data.RawParticulars || particular,
            mainCategory: codeRes.data.mainCategory || codeRes.data.standardizedCode || mainCat || "",
            category1: codeRes.data.category1 || brdCls || "",
            category2: codeRes.data.category2 || brdCls2 || "",
            category3: codeRes.data.category3 || ctgCode || "",
            category4: codeRes.data.category4 || caFlFnFl || "",
            category5: codeRes.data.category5 || cat5 || "",
          };
        }
      } catch (error: any) {
        // If lookup fails, use row data (don't show error)
        console.log("No existing code master found for particular:", particular);
      }
    }
    
    setCodeForm(formData);
    setSelectedRowForAdd({ row, index: rowIndex });
    setAddDataDialogOpen(true);
  };

  // Handle export to Excel
  const handleExportToExcel = async () => {
    try {
      setIsExporting(true);
      const entityId = selectedEntity && selectedEntity !== "all" ? parseInt(selectedEntity) : undefined;
      const financialYear = selectedYear && selectedYear !== "all" ? parseInt(selectedYear) : undefined;
      
      // Get entity code if entityId is selected
      let entityCode = undefined;
      if (entityId) {
        const entity = entities.find(e => e.ent_id === entityId);
        entityCode = entity?.ent_code;
      }
      
      // Call the export API
      const blob = await structuredDataApi.exportToExcel(entityId, financialYear, entityCode);
      
      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `structured_data_export_${timestamp}.xlsx`;
      link.download = filename;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast({
        title: "Export successful",
        description: `Excel file downloaded successfully.`,
      });
    } catch (error: any) {
      console.error("Error exporting to Excel:", error);
      toast({
        title: "Export failed",
        description: error.message || "Failed to export data to Excel. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Handle save code from add data dialog
  const handleSaveCode = async () => {
    try {
      if (!codeForm.RawParticulars || !codeForm.mainCategory) {
        toast({ 
          title: "Missing fields", 
          description: "Raw Particulars and Main Category are required", 
          variant: "destructive" 
        });
        return;
      }

      setIsSavingCode(true);
      const particular = codeForm.RawParticulars.trim();
      
      // Step 1: Save code to code master
      const res = await codeMasterApi.create({
        RawParticulars: particular,
        mainCategory: codeForm.mainCategory,
        category1: codeForm.category1 || undefined,
        category2: codeForm.category2 || undefined,
        category3: codeForm.category3 || undefined,
        category4: codeForm.category4 || undefined,
        category5: codeForm.category5 || undefined,
      });

      if (res.success) {
        // Step 2: Update final_structured table with the new code data
        try {
          const updateRes = await structuredDataApi.updateByParticular(particular);
          
          if (updateRes.success) {
            const updatedCount = updateRes.data?.updated_count || 0;
            toast({ 
              title: "Code saved and data updated successfully", 
              description: `Code saved to master. Updated ${updatedCount} row(s) in structured data.` 
            });
            
            // Step 3: Refresh structured data to show updated values
            await fetchStructuredData();
          } else {
            toast({ 
              title: "Code saved but update failed", 
              description: "Code saved to master, but failed to update structured data. Please refresh manually.",
              variant: "destructive"
            });
          }
        } catch (updateError: any) {
          console.error("Error updating structured data:", updateError);
          toast({ 
            title: "Code saved but update failed", 
            description: updateError.message || "Code saved to master, but failed to update structured data. Please refresh manually.",
            variant: "destructive"
          });
        }
        
        // Close dialog and reset form
        setAddDataDialogOpen(false);
        setCodeForm({
          RawParticulars: "",
          mainCategory: "",
          category1: "",
          category2: "",
          category3: "",
          category4: "",
          category5: "",
        });
        setSelectedRowForAdd(null);
        
        // Refresh unique values after adding new code
        fetchUniqueValues();
      }
    } catch (e: any) {
      toast({ 
        title: "Save failed", 
        description: e.message || "Failed to save code", 
        variant: "destructive" 
      });
    } finally {
      setIsSavingCode(false);
    }
  };

  const handleDeleteAll = async () => {
    try {
      setIsDeletingAll(true);
      const res = await structuredDataApi.deleteAll();
      if (res.success) {
        const deletedCount = res.data?.deleted_count || 0;
        const rawdataCount = res.data?.rawdata_count || 0;
        const finalStructuredCount = res.data?.final_structured_count || 0;
        toast({ 
          title: "All data deleted", 
          description: `Successfully deleted ${rawdataCount} record(s) from rawdata and ${finalStructuredCount} record(s) from final_structured.`,
        });
        setDeleteAllDialogOpen(false);
        // Refresh data after deletion
        await fetchStructuredData();
      }
    } catch (e: any) {
      toast({ 
        title: "Delete all failed", 
        description: e.message || "Failed to delete all data", 
        variant: "destructive" 
      });
    } finally {
      setIsDeletingAll(false);
    }
  };

  return (
    <div className="p-6 space-y-6 bg-gradient-to-br from-background via-background to-muted/30 min-h-full">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">Structured Data</h1>
          <p className="text-muted-foreground mt-1">View processed balance sheet data</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedEntity} onValueChange={setSelectedEntity}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Entities" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Entities</SelectItem>
              {entities.map((entity) => (
                <SelectItem key={entity.ent_id} value={entity.ent_id.toString()}>
                  {entity.ent_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All Years" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Years</SelectItem>
              {financialYears.map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  FY {year}-{(year + 1).toString().slice(-2)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-0 shadow-md card-hover bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Assets</CardTitle>
            <div className="p-2.5 rounded-lg bg-success-light"><TrendingUp className="h-5 w-5 text-success" /></div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {isLoading ? "Loading..." : formatTotalAssets(totalAssets)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {filteredData.length} {filteredData.length !== balanceSheetData.length ? `of ${balanceSheetData.length} ` : ""}records
            </p>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md card-hover bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Missing Rows</CardTitle>
            <div className="p-2.5 rounded-lg bg-destructive/10"><AlertTriangle className="h-5 w-5 text-destructive" /></div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-destructive">
              {isLoading ? "Loading..." : missingRowsCount}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Rows with at least one missing value (Avg Fx Rt excluded)
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border shadow-lg bg-card">
        <CardHeader className="border-b bg-gradient-to-r from-primary/5 via-primary/3 to-transparent">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <CardTitle className="flex items-center gap-2 text-lg font-bold">
                <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                  <DollarSign className="h-5 w-5 text-primary" />
                </div>
                Structured Data
              </CardTitle>
              <div className="flex items-center gap-2">
                <Label className="text-xs text-muted-foreground">Main Category</Label>
                <Select
                  value={mainCategoryFilter}
                  onValueChange={(val) => setMainCategoryFilter(val as "all" | "missing" | "available")}
                >
                  <SelectTrigger className="h-8 w-[130px] text-xs">
                    <SelectValue placeholder="All" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="missing">Missing</SelectItem>
                    <SelectItem value="available">Available</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setDeleteAllDialogOpen(true)}
                disabled={isLoading || balanceSheetData.length === 0}
                className="gap-2"
              >
                <Trash className="h-4 w-4" />
                Delete All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportToExcel}
                disabled={isExporting || isLoading || balanceSheetData.length === 0}
                className="gap-2"
              >
                <Download className="h-4 w-4" />
                {isExporting ? "Exporting..." : "Export Excel"}
              </Button>
              {Object.keys(columnFilters).length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllFilters}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear Filters
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0 relative">
          <div className="w-full overflow-hidden [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          <Table className="w-full border-collapse" style={{ tableLayout: 'auto', width: '100%', wordWrap: 'break-word' }}>
            <TableHeader>
              {/* Header row with column names */}
              <TableRow className="hover:bg-transparent bg-muted/50 border-b-2 border-border">
                {columns.length > 0 ? (
                  columns.map((col) => {
                    const isAmount = /(^|_)(transactionamount|amt|amount)(_|$)/i.test(col);
                    const isSerialNo = /sl_no/i.test(col);
                    return (
                      <TableHead
                        key={col}
                        draggable
                        onDragStart={() => setDraggingCol(col)}
                        onDragOver={(e) => {
                          e.preventDefault();
                          e.dataTransfer.dropEffect = "move";
                        }}
                        onDrop={(e) => {
                          e.preventDefault();
                          if (draggingCol) reorderColumns(draggingCol, col);
                          setDraggingCol(null);
                        }}
                        className={`${isAmount ? "text-right" : isSerialNo ? "text-center" : ""} break-words font-semibold text-foreground cursor-move`}
                        style={{ 
                          wordWrap: 'break-word',
                          maxWidth: isSerialNo ? '40px' : isAmount ? '90px' : '100px',
                          fontSize: '0.74rem',
                          padding: '8px 6px',
                          backgroundColor: 'hsl(var(--muted))',
                          borderRight: '1px solid hsl(var(--border))'
                        }}
                      >
                        <div className="flex items-center justify-between gap-1">
                          <div className="text-xs font-semibold leading-tight text-foreground break-words text-left">{humanizeColumnName(col)}</div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                            onClick={() => setColumns((prev) => prev.filter((c) => c !== col))}
                            title="Hide column"
                          >
                            <X className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableHead>
                    );
                  })
                ) : (
                  <>
                    <TableHead className="text-center">Sl No</TableHead>
                    <TableHead>Particular</TableHead>
                    <TableHead className="text-right">Transaction Amount</TableHead>
                    <TableHead>Entity Name</TableHead>
                    <TableHead>Local Currency Code</TableHead>
                    <TableHead>Main Category</TableHead>
                    <TableHead>Category 1</TableHead>
                    <TableHead>Category 2</TableHead>
                    <TableHead>Category 3</TableHead>
                    <TableHead>Category 4</TableHead>
                    <TableHead>Category 5</TableHead>
                    <TableHead>Avg Fx Rt</TableHead>
                    <TableHead className="text-right">Transaction Amount USD</TableHead>
                    <TableHead>Month</TableHead>
                    <TableHead>Year</TableHead>
                  </>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={columns.length || 14} className="text-center py-8 text-muted-foreground">
                    Loading data...
                  </TableCell>
                </TableRow>
              ) : filteredData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns.length || 14} className="text-center py-8 text-muted-foreground">
                    {balanceSheetData.length === 0 
                      ? "No data available. Please ensure the final_structured table has data."
                      : "No records match the current filters."}
                  </TableCell>
                </TableRow>
              ) : (
                filteredData.map((row, i) => {
                  // Check if this row has any missing data (excluding avg_fx_rt)
                  const rowHasMissingData = (columns.length > 0 ? columns : Object.keys(row || {})).some((col) => {
                    // Skip avg_fx_rt from row highlighting check
                    if (/avg_fx_rt/i.test(col)) return false;
                    const value = (row as any)[col];
                    return isMissingValue(col, value);
                  });

                  const isHovered = hoveredRowIndex === i;
                  
                  // Add light red background to entire row if it has missing data
                  const rowClasses = rowHasMissingData 
                    ? 'bg-red-50/50 dark:bg-red-950/10 hover:bg-red-100/70 dark:hover:bg-red-950/20 group border-b border-border/50' 
                    : 'hover:bg-muted/30 border-b border-border/30 transition-colors';

                  return (
                    <TableRow 
                      key={i} 
                      className={`${rowClasses} relative`}
                      onMouseEnter={() => rowHasMissingData && setHoveredRowIndex(i)}
                      onMouseLeave={() => setHoveredRowIndex(null)}
                    >
                      {(columns.length > 0 ? columns : Object.keys(row || {})).map((col) => {
                        const value = (row as any)[col];
                        const isAmount = /(^|_)(transactionamount|amt|amount)(_|$)/i.test(col);
                        const isSerialNo = /sl_no/i.test(col);
                        
                        // For serial number, always use filtered row index + 1 for better UX when filtering
                        const displayValue = isSerialNo 
                          ? (i + 1).toString() 
                          : value;
                        
                        // Determine alignment: serial number centers, amount right-aligns, others left
                        let alignmentClass = "";
                        if (isSerialNo) {
                          alignmentClass = "text-center";
                        } else if (isAmount) {
                          alignmentClass = "text-right";
                        }
                        
                        return (
                          <TableCell
                            key={col}
                            className={`${alignmentClass} break-words`}
                            style={{ 
                              wordWrap: 'break-word',
                            maxWidth: isSerialNo ? '40px' : isAmount ? '90px' : '90px',
                            fontSize: '0.72rem',
                            padding: '8px 6px',
                              borderRight: '1px solid hsl(var(--border) / 0.3)',
                              verticalAlign: 'middle'
                            }}
                          >
                            {isAmount ? (
                              <span className="font-semibold text-xs text-foreground">{renderCellValue(col, displayValue)}</span>
                            ) : (
                              <div className="text-xs leading-tight text-foreground/90">{renderCellValue(col, displayValue)}</div>
                            )}
                          </TableCell>
                        );
                      })}
                      {/* Add button that slides in from right on hover */}
                      {rowHasMissingData && (
                        <TableCell 
                          className="p-0 w-1 relative"
                          style={{ position: 'relative', overflow: 'visible', padding: 0 }}
                        >
                          <div 
                            className={`absolute right-0 top-0 bottom-0 flex items-center justify-end transition-all duration-300 ease-in-out z-10 ${
                              isHovered 
                                ? 'translate-x-0 opacity-100 pointer-events-auto' 
                                : 'translate-x-full opacity-0 pointer-events-none'
                            }`}
                            style={{ right: 0 }}
                          >
                            <Button
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAddData(i, row);
                              }}
                              className="h-8 rounded-l-lg rounded-r-none bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg px-3 sm:px-4 gap-2 whitespace-nowrap"
                            >
                              <Plus className="h-4 w-4" />
                              <span className="hidden sm:inline">Add Data</span>
                            </Button>
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
          </div>
        </CardContent>
      </Card>

      {/* Add Code Dialog */}
      <Dialog open={addDataDialogOpen} onOpenChange={setAddDataDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Add Code to Master</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
            <div className="space-y-2 md:col-span-2">
              <Label>Raw Particulars *</Label>
              <Input 
                value={codeForm.RawParticulars} 
                onChange={(e) => setCodeForm({ ...codeForm, RawParticulars: e.target.value })} 
                placeholder="Bank Charges" 
              />
            </div>
            <div className="space-y-2">
              <Label>Main Category *</Label>
              <Combobox
                value={codeForm.mainCategory}
                onValueChange={(value) => setCodeForm({ ...codeForm, mainCategory: value })}
                options={uniqueValues.mainCategory}
                placeholder="Type or select main category..."
                searchPlaceholder="Search main categories..."
                emptyMessage="No main categories found. Type to create new."
              />
            </div>
            <div className="space-y-2">
              <Label>Category 1</Label>
              <Combobox
                value={codeForm.category1}
                onValueChange={(value) => setCodeForm({ ...codeForm, category1: value })}
                options={uniqueValues.category1}
                placeholder="Type or select category 1..."
                searchPlaceholder="Search categories..."
                emptyMessage="No categories found. Type to create new."
              />
            </div>
            <div className="space-y-2">
              <Label>Category 2</Label>
              <Combobox
                value={codeForm.category2}
                onValueChange={(value) => setCodeForm({ ...codeForm, category2: value })}
                options={uniqueValues.category2}
                placeholder="Type or select category 2..."
                searchPlaceholder="Search categories..."
                emptyMessage="No categories found. Type to create new."
              />
            </div>
            <div className="space-y-2">
              <Label>Category 3</Label>
              <Combobox
                value={codeForm.category3}
                onValueChange={(value) => setCodeForm({ ...codeForm, category3: value })}
                options={uniqueValues.category3}
                placeholder="Type or select category 3..."
                searchPlaceholder="Search categories..."
                emptyMessage="No categories found. Type to create new."
              />
            </div>
            <div className="space-y-2">
              <Label>Category 4</Label>
              <Combobox
                value={codeForm.category4}
                onValueChange={(value) => setCodeForm({ ...codeForm, category4: value })}
                options={uniqueValues.category4}
                placeholder="Type or select category 4..."
                searchPlaceholder="Search categories..."
                emptyMessage="No categories found. Type to create new."
              />
            </div>
            <div className="space-y-2">
              <Label>Category 5</Label>
              <Combobox
                value={codeForm.category5}
                onValueChange={(value) => setCodeForm({ ...codeForm, category5: value })}
                options={uniqueValues.category5}
                placeholder="Type or select category 5..."
                searchPlaceholder="Search categories..."
                emptyMessage="No categories found. Type to create new."
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => {
                setAddDataDialogOpen(false);
                setCodeForm({
                  RawParticulars: "",
                  mainCategory: "",
                  category1: "",
                  category2: "",
                  category3: "",
                  category4: "",
                  category5: "",
                });
                setSelectedRowForAdd(null);
              }}
            >
              Cancel
            </Button>
            <Button 
              className="gradient-primary text-white" 
              onClick={handleSaveCode}
              disabled={isSavingCode}
            >
              {isSavingCode ? "Saving..." : "Save Code"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete All Confirmation Dialog */}
      <AlertDialog open={deleteAllDialogOpen} onOpenChange={setDeleteAllDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete All Data?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete <strong>all records</strong> from both the <strong>rawdata</strong> and <strong>final_structured</strong> tables.
              <br /><br />
              This is a destructive operation that will remove all uploaded and processed data.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteAllDialogOpen(false)}>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteAll} 
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isDeletingAll}
            >
              {isDeletingAll ? "Deleting..." : "Delete All"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
