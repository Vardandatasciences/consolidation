import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, DollarSign, Calendar, Building2, RefreshCcw, Loader2, MoreVertical } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from "react";
import { forexApi, entityApi, uploadApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type Entity = {
  ent_id: number;
  ent_name: string;
  ent_code: string;
  lcl_curr: string;
  financial_year_start_month?: number;
  financial_year_start_day?: number;
};

type ForexRate = {
  id: number;
  entity_id: number;
  currency: string;
  financial_year: number | string; // Can be number (ending year like 2024) or string ("2024-25")
  opening_rate: number;
  closing_rate: number;
  fy_start_date: string;
  fy_end_date: string;
  created_at: string;
  updated_at: string;
};


export default function Forex() {
  const { toast } = useToast();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [financialYears, setFinancialYears] = useState<number[]>([]);
  const [selectedEntityId, setSelectedEntityId] = useState<number | null>(null);
  const [rates, setRates] = useState<ForexRate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editingRate, setEditingRate] = useState<ForexRate | null>(null);
  const [form, setForm] = useState({
    currency: "",
    opening_rate: "",
    closing_rate: "",
    financial_year: "",
  });
  const [editForm, setEditForm] = useState({
    currency: "",
    opening_rate: "",
    closing_rate: "",
    financial_year: "",
  });

  useEffect(() => {
    loadEntities();
    loadFinancialYears();
  }, []);

  useEffect(() => {
    if (selectedEntityId) {
      loadRates();
    } else {
      setRates([]);
    }
  }, [selectedEntityId]);

  const loadEntities = async () => {
    try {
      const res = await entityApi.list();
      if (res.success && res.data?.entities) {
        setEntities(res.data.entities);
      }
    } catch (e: any) {
      toast({
        title: "Failed to load entities",
        description: e.message || "Could not fetch entities",
        variant: "destructive",
      });
    }
  };

  const loadFinancialYears = async () => {
    try {
      const res = await uploadApi.getFinancialYears();
      if (res.success && res.data?.years) {
        setFinancialYears(res.data.years);
      }
    } catch (e: any) {
      console.error("Failed to load financial years:", e);
    }
  };

  const loadRates = async () => {
    if (!selectedEntityId) return;

    try {
      setIsLoading(true);
      const res = await forexApi.getEntityAllRates(selectedEntityId);
      if (res.success && res.data?.rates) {
        setRates(res.data.rates);
      }
    } catch (e: any) {
      toast({
        title: "Failed to load forex rates",
        description: e.message || "Could not fetch rates",
        variant: "destructive",
      });
      setRates([]);
    } finally {
      setIsLoading(false);
    }
  };

  const getSelectedEntity = (): Entity | null => {
    return entities.find((e) => e.ent_id === selectedEntityId) || null;
  };

  const onCreate = async () => {
    if (!selectedEntityId) {
      toast({
        title: "Selection required",
        description: "Please select an entity",
        variant: "destructive",
      });
      return;
    }

    try {
      if (!form.currency || !form.opening_rate || !form.closing_rate || !form.financial_year) {
        toast({
          title: "Missing fields",
          description: "Currency, financial year, opening rate, and closing rate are required",
          variant: "destructive",
        });
        return;
      }

      const openingRate = parseFloat(form.opening_rate);
      const closingRate = parseFloat(form.closing_rate);
      const financialYear = parseInt(form.financial_year, 10);

      if (isNaN(openingRate) || isNaN(closingRate) || isNaN(financialYear)) {
        toast({
          title: "Invalid values",
          description: "Opening rate, closing rate, and financial year must be valid numbers",
          variant: "destructive",
        });
        return;
      }

      const payload = {
        currency: form.currency.toUpperCase(),
        opening_rate: openingRate,
        closing_rate: closingRate,
      };

      const res = await forexApi.setEntityFYRates(selectedEntityId, financialYear, payload);

      if (res.success) {
        toast({ title: "Forex rates created successfully" });
        setOpen(false);
        setForm({ currency: "", opening_rate: "", closing_rate: "", financial_year: "" });
        loadRates();
      }
    } catch (e: any) {
      toast({
        title: "Create failed",
        description: e.message || "Unable to create forex rates",
        variant: "destructive",
      });
    }
  };

  const handleEdit = (rate: ForexRate) => {
    setEditingRate(rate);
    // Parse financial year - handle both string and number formats
    let fyValue = "";
    if (typeof rate.financial_year === 'string' && rate.financial_year.includes('-')) {
      // Extract ending year from "2024-25" format
      const parts = rate.financial_year.split('-');
      fyValue = parts[0];
    } else {
      fyValue = rate.financial_year.toString();
    }
    
    setEditForm({
      currency: rate.currency,
      opening_rate: rate.opening_rate.toString(),
      closing_rate: rate.closing_rate.toString(),
      financial_year: fyValue,
    });
    setEditOpen(true);
  };

  const handleUpdate = async () => {
    if (!editingRate) return;

    if (!editForm.currency || !editForm.opening_rate || !editForm.closing_rate || !editForm.financial_year) {
      toast({
        title: "Missing fields",
        description: "All fields are required",
        variant: "destructive",
      });
      return;
    }

    const openingRate = parseFloat(editForm.opening_rate);
    const closingRate = parseFloat(editForm.closing_rate);
    const financialYear = parseInt(editForm.financial_year, 10);

    if (isNaN(openingRate) || isNaN(closingRate) || isNaN(financialYear)) {
      toast({
        title: "Invalid values",
        description: "Opening rate, closing rate, and financial year must be valid numbers",
        variant: "destructive",
      });
      return;
    }

    try {
      const payload = {
        currency: editForm.currency.toUpperCase(),
        opening_rate: openingRate,
        closing_rate: closingRate,
      };

      const res = await forexApi.updateEntityFYRates(editingRate.entity_id, financialYear, payload);
      if (res.success) {
        toast({ title: "Forex rate updated successfully" });
        setEditOpen(false);
        setEditingRate(null);
        loadRates();
      }
    } catch (e: any) {
      toast({
        title: "Update failed",
        description: e.message || "Unable to update forex rate",
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

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6,
    }).format(value);
  };

  const formatFinancialYear = (year: number | string) => {
    // Handle string format like "2024-25"
    if (typeof year === 'string' && year.includes('-')) {
      return `FY ${year}`;
    }
    // Handle number format - backend uses starting year convention
    // If year = 2024, it means FY 2024-25 (not 2023-24)
    const yearNum = typeof year === 'string' ? parseInt(year, 10) : year;
    if (isNaN(yearNum)) return String(year);
    const nextYear = yearNum + 1;
    const nextYearStr = nextYear.toString().slice(-2);
    return `FY ${yearNum}-${nextYearStr}`;
  };

  const selectedEntity = getSelectedEntity();
  const defaultCurrency = selectedEntity?.lcl_curr || "";

  return (
    <div className="page-shell">
      <div className="toolbar-stack">
        <div>
          <h1 className="page-title text-3xl sm:text-4xl">Forex Rates</h1>
          <p className="subtle-text mt-1">Manage financial year based forex rates per entity</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <Select
            value={selectedEntityId?.toString() || ""}
            onValueChange={(val) => setSelectedEntityId(val ? parseInt(val) : null)}
          >
            <SelectTrigger className="w-[250px]">
              <SelectValue placeholder="Select Entity" />
            </SelectTrigger>
            <SelectContent>
              {entities.map((ent) => (
                <SelectItem key={ent.ent_id} value={ent.ent_id.toString()}>
                  {ent.ent_name} ({ent.ent_code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" className="gap-2" onClick={loadRates} disabled={isLoading || !selectedEntityId}>
            <RefreshCcw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {selectedEntity && (
        <Card className="border-0 shadow-md mb-4">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label className="text-sm text-muted-foreground">Entity</Label>
                <p className="font-medium">{selectedEntity.ent_name}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Local Currency</Label>
                <p className="font-medium">{selectedEntity.lcl_curr}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">FY Start</Label>
                <p className="font-medium">
                  {selectedEntity.financial_year_start_month
                    ? `Month ${selectedEntity.financial_year_start_month}, Day ${selectedEntity.financial_year_start_day || 1}`
                    : "Not configured"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary-light">
                <DollarSign className="h-5 w-5 text-primary" />
              </div>
              Forex Rates
              {selectedEntityId && (
                <Badge variant="outline" className="ml-2">
                  {rates.length} rate{rates.length !== 1 ? "s" : ""}
                </Badge>
              )}
            </CardTitle>
            {selectedEntityId && (
              <Dialog open={open} onOpenChange={setOpen}>
                <DialogTrigger asChild>
                  <Button className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add Rate
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Forex Rate</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="financial_year">Financial Year (Ending Year) *</Label>
                      <Select
                        value={form.financial_year}
                        onValueChange={(value) => setForm({ ...form, financial_year: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select Financial Year" />
                        </SelectTrigger>
                        <SelectContent>
                          {financialYears.map((year) => (
                            <SelectItem key={year} value={year.toString()}>
                              FY {year - 1}-{year.toString().slice(-2)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="currency">Currency *</Label>
                      <Input
                        id="currency"
                        value={form.currency}
                        onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })}
                        placeholder={defaultCurrency || "USD"}
                      />
                      {defaultCurrency && (
                        <p className="text-xs text-muted-foreground">Entity default: {defaultCurrency}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="opening_rate">Opening Rate (FY Start) *</Label>
                      <Input
                        id="opening_rate"
                        type="number"
                        step="0.000001"
                        value={form.opening_rate}
                        onChange={(e) => setForm({ ...form, opening_rate: e.target.value })}
                        placeholder="82.50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="closing_rate">Closing Rate (FY End) *</Label>
                      <Input
                        id="closing_rate"
                        type="number"
                        step="0.000001"
                        value={form.closing_rate}
                        onChange={(e) => setForm({ ...form, closing_rate: e.target.value })}
                        placeholder="83.20"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={onCreate}>Create</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {!selectedEntityId ? (
            <div className="p-8 text-center text-muted-foreground">
              <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Please select an entity to view forex rates</p>
            </div>
          ) : isLoading ? (
            <div className="p-8 text-center">
              <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
              <p className="mt-2 text-muted-foreground">Loading rates...</p>
            </div>
          ) : rates.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <DollarSign className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No forex rates configured for this entity</p>
              <p className="text-sm mt-2">Click "Add Rate" to create one</p>
            </div>
          ) : (
            <div className="table-responsive">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Financial Year</TableHead>
                    <TableHead>Currency</TableHead>
                    <TableHead>Opening Rate</TableHead>
                    <TableHead>Closing Rate</TableHead>
                    <TableHead>Average (P&L)</TableHead>
                    <TableHead>FY Start Date</TableHead>
                    <TableHead>FY End Date</TableHead>
                    <TableHead>Last Updated</TableHead>
                    <TableHead className="w-[50px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rates.map((rate) => {
                    const opening = parseFloat(rate.opening_rate) || 0;
                    const closing = parseFloat(rate.closing_rate) || 0;
                    const avgRate = (opening + closing) / 2;
                    return (
                      <RateRow 
                        key={rate.id} 
                        rate={rate} 
                        avgRate={avgRate} 
                        onEdit={handleEdit}
                        formatCurrency={formatCurrency} 
                        formatDate={formatDate}
                        formatFinancialYear={formatFinancialYear}
                      />
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Forex Rate</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit_financial_year">Financial Year (Ending Year) *</Label>
              <Select
                value={editForm.financial_year}
                onValueChange={(value) => setEditForm({ ...editForm, financial_year: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Financial Year" />
                </SelectTrigger>
                <SelectContent>
                  {financialYears.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      FY {year - 1}-{year.toString().slice(-2)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit_currency">Currency *</Label>
              <Input
                id="edit_currency"
                value={editForm.currency}
                onChange={(e) => setEditForm({ ...editForm, currency: e.target.value.toUpperCase() })}
                placeholder="USD"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit_opening_rate">Opening Rate (FY Start) *</Label>
              <Input
                id="edit_opening_rate"
                type="number"
                step="0.000001"
                value={editForm.opening_rate}
                onChange={(e) => setEditForm({ ...editForm, opening_rate: e.target.value })}
                placeholder="82.50"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit_closing_rate">Closing Rate (FY End) *</Label>
              <Input
                id="edit_closing_rate"
                type="number"
                step="0.000001"
                value={editForm.closing_rate}
                onChange={(e) => setEditForm({ ...editForm, closing_rate: e.target.value })}
                placeholder="83.20"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setEditOpen(false);
              setEditingRate(null);
            }}>
              Cancel
            </Button>
            <Button onClick={handleUpdate}>Update</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function RateRow({
  rate,
  avgRate,
  onEdit,
  formatCurrency,
  formatDate,
  formatFinancialYear,
}: {
  rate: ForexRate;
  avgRate: number;
  onEdit: (rate: ForexRate) => void;
  formatCurrency: (value: number) => string;
  formatDate: (dateString: string) => string;
  formatFinancialYear: (year: number | string) => string;
}) {
  return (
    <TableRow className="hover:bg-muted/50">
      <TableCell className="font-medium">
        {formatFinancialYear(rate.financial_year)}
      </TableCell>
      <TableCell className="font-medium">
        <Badge variant="outline">{rate.currency}</Badge>
      </TableCell>
      <TableCell>
            {formatCurrency(rate.opening_rate)}
      </TableCell>
      <TableCell>
            {formatCurrency(rate.closing_rate)}
      </TableCell>
      <TableCell className="text-muted-foreground">{formatCurrency(avgRate)}</TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          {formatDate(rate.fy_start_date)}
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          {formatDate(rate.fy_end_date)}
        </div>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground">{formatDate(rate.updated_at)}</TableCell>
      <TableCell>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit(rate)}>
              Edit
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}

