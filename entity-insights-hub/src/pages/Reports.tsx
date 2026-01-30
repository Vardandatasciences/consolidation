import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrendingUp, AlertTriangle, Download, Loader2 } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useState, useEffect } from "react";
import { reportsApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type Metric = { value: string; label: string; category: string };
type FinancialYear = { value: string; label: string; year: number };
type Entity = { ent_id: number; ent_name: string; ent_code: string };
type ComparisonData = {
  entity_code: string;
  entity_name: string;
  total_amount: number;
  total_amount_usd: number;
  record_count: number;
};
type AlertData = {
  type: 'warning' | 'error' | 'info';
  severity: 'low' | 'medium' | 'high';
  entity_code: string;
  entity_name: string;
  title: string;
  message: string;
  metric: string;
  value: number;
};

export default function Reports() {
  const { toast } = useToast();
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [years, setYears] = useState<FinancialYear[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>("total-amount");
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [reportType, setReportType] = useState<string>("comparison");
  const [comparisonData, setComparisonData] = useState<ComparisonData[]>([]);
  const [comparisonSummary, setComparisonSummary] = useState<{
    entity_count: number;
    total_amount: number;
    total_amount_usd: number;
    average_amount: number;
  } | null>(null);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [loadingComparison, setLoadingComparison] = useState(false);
  const [loadingAlerts, setLoadingAlerts] = useState(false);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoadingMetrics(true);
        const [metricsRes, yearsRes, entitiesRes] = await Promise.all([
          reportsApi.getMetrics(),
          reportsApi.getFinancialYears(),
          reportsApi.getEntities(),
        ]);

        if (metricsRes.success && metricsRes.data?.metrics) {
          setMetrics(metricsRes.data.metrics);
        }
        if (yearsRes.success && yearsRes.data?.years) {
          setYears(yearsRes.data.years);
          // Set default to latest year
          if (yearsRes.data.years.length > 0) {
            setSelectedYear(yearsRes.data.years[0].value);
          }
        }
        if (entitiesRes.success && entitiesRes.data?.entities) {
          setEntities(entitiesRes.data.entities);
        }
      } catch (error: any) {
        toast({
          title: "Failed to load report data",
          description: error.message,
          variant: "destructive",
        });
      } finally {
        setLoadingMetrics(false);
      }
    };

    loadInitialData();
  }, [toast]);

  // Load comparison data when selections change
  useEffect(() => {
    if (selectedMetric && selectedYear && reportType === "comparison") {
      loadComparisonData();
    }
  }, [selectedMetric, selectedYear, reportType]);

  // Load alerts
  useEffect(() => {
    loadAlerts();
  }, [selectedYear]);

  const loadComparisonData = async () => {
    try {
      setLoadingComparison(true);
      const yearNum = years.find((y) => y.value === selectedYear)?.year;
      if (!yearNum) return;

      const res = await reportsApi.getComparison(selectedMetric, yearNum);
      if (res.success && res.data) {
        setComparisonData(res.data.comparison_data || []);
        setComparisonSummary(res.data.summary || null);
      }
    } catch (error: any) {
      toast({
        title: "Failed to load comparison data",
        description: error.message,
        variant: "destructive",
      });
      setComparisonData([]);
      setComparisonSummary(null);
    } finally {
      setLoadingComparison(false);
    }
  };

  const loadAlerts = async () => {
    try {
      setLoadingAlerts(true);
      const yearNum = years.find((y) => y.value === selectedYear)?.year;
      const res = await reportsApi.getAlerts(yearNum);
      if (res.success && res.data) {
        setAlerts(res.data.alerts || []);
      }
    } catch (error: any) {
      toast({
        title: "Failed to load alerts",
        description: error.message,
        variant: "destructive",
      });
      setAlerts([]);
    } finally {
      setLoadingAlerts(false);
    }
  };

  const handleExport = async () => {
    try {
      const yearNum = years.find((y) => y.value === selectedYear)?.year;
      const res = await reportsApi.exportReport(selectedMetric, yearNum);
      
      if (res.success) {
        toast({
          title: "Export initiated",
          description: "Report export functionality is available",
        });
        // In a full implementation, this would download a file
        // For now, we can create a CSV from comparison data
        if (comparisonData.length > 0) {
          const csv = generateCSV();
          downloadCSV(csv, `report-${selectedMetric}-${yearNum || 'all'}.csv`);
        }
      }
    } catch (error: any) {
      toast({
        title: "Export failed",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const generateCSV = (): string => {
    const headers = ["Entity Code", "Entity Name", "Total Amount", "Total Amount (USD)", "Record Count"];
    const rows = comparisonData.map((row) => [
      row.entity_code,
      row.entity_name,
      row.total_amount.toLocaleString(),
      row.total_amount_usd.toLocaleString(),
      row.record_count.toString(),
    ]);

    return [headers, ...rows].map((row) => row.join(",")).join("\n");
  };

  const downloadCSV = (csv: string, filename: string) => {
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatCurrencyUSD = (amount: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getAlertVariant = (type: string): "default" | "destructive" => {
    return type === "error" ? "destructive" : "default";
  };

  const getAlertBorderClass = (type: string, severity: string): string => {
    if (type === "error" || severity === "high") {
      return "border-destructive/50 bg-destructive/5";
    }
    if (type === "warning" || severity === "medium") {
      return "border-warning/50 bg-warning/5";
    }
    return "border-primary/50 bg-primary/5";
  };

  return (
    <div className="page-shell">
      <div className="toolbar-stack">
        <div>
          <h1 className="page-title text-3xl sm:text-4xl">Reports & Analytics</h1>
          <p className="subtle-text mt-1">Deep analysis and comparisons</p>
        </div>
        <Button
          className="gap-2 gradient-primary text-white shadow-primary"
          onClick={handleExport}
          disabled={!comparisonData.length || loadingComparison}
        >
          {loadingComparison ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          Export Report
        </Button>
      </div>

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary-light">
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            Report Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Metric</label>
              <Select
                value={selectedMetric}
                onValueChange={setSelectedMetric}
                disabled={loadingMetrics}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select metric" />
                </SelectTrigger>
                <SelectContent>
                  {metrics.map((metric) => (
                    <SelectItem key={metric.value} value={metric.value}>
                      {metric.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Period</label>
              <Select
                value={selectedYear}
                onValueChange={setSelectedYear}
                disabled={loadingMetrics || years.length === 0}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select financial year" />
                </SelectTrigger>
                <SelectContent>
                  {years.map((year) => (
                    <SelectItem key={year.value} value={year.value}>
                      {year.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Report Type</label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="comparison">Cross-Entity Comparison</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {reportType === "comparison" && (
        <Card className="border-0 shadow-md">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle>Comparison Results</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {loadingComparison ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <span className="ml-2 text-muted-foreground">Loading comparison data...</span>
              </div>
            ) : comparisonData.length > 0 ? (
              <div className="space-y-4">
                {comparisonSummary && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-muted/50 rounded-lg">
                    <div>
                      <p className="text-sm text-muted-foreground">Entities</p>
                      <p className="text-2xl font-bold">{comparisonSummary.entity_count}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Amount</p>
                      <p className="text-2xl font-bold">{formatCurrency(comparisonSummary.total_amount)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total (USD)</p>
                      <p className="text-2xl font-bold">{formatCurrencyUSD(comparisonSummary.total_amount_usd)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Average</p>
                      <p className="text-2xl font-bold">{formatCurrency(comparisonSummary.average_amount)}</p>
                    </div>
                  </div>
                )}
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Entity Code</TableHead>
                        <TableHead>Entity Name</TableHead>
                        <TableHead className="text-right">Total Amount</TableHead>
                        <TableHead className="text-right">Total (USD)</TableHead>
                        <TableHead className="text-right">Records</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {comparisonData.map((row, idx) => (
                        <TableRow key={`${row.entity_code}-${idx}`}>
                          <TableCell className="font-medium">{row.entity_code}</TableCell>
                          <TableCell>{row.entity_name}</TableCell>
                          <TableCell className="text-right">{formatCurrency(row.total_amount)}</TableCell>
                          <TableCell className="text-right">{formatCurrencyUSD(row.total_amount_usd)}</TableCell>
                          <TableCell className="text-right">{row.record_count.toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No comparison data available. Please select a metric and financial year.
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-r from-warning/5 to-transparent">
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-warning-light">
              <AlertTriangle className="h-5 w-5 text-warning" />
            </div>
            Red Flags & Alerts
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 pt-6">
          {loadingAlerts ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span className="ml-2 text-sm text-muted-foreground">Loading alerts...</span>
            </div>
          ) : alerts.length > 0 ? (
            alerts.map((alert, idx) => (
              <Alert
                key={`alert-${idx}`}
                variant={getAlertVariant(alert.type)}
                className={getAlertBorderClass(alert.type, alert.severity)}
              >
                <AlertTriangle
                  className={`h-4 w-4 ${
                    alert.type === "error" || alert.severity === "high"
                      ? "text-destructive"
                      : alert.type === "warning" || alert.severity === "medium"
                      ? "text-warning"
                      : "text-primary"
                  }`}
                />
                <AlertDescription>
                  <strong>{alert.entity_name || alert.entity_code}:</strong> {alert.message}
                </AlertDescription>
              </Alert>
            ))
          ) : (
            <div className="text-center py-4 text-muted-foreground">
              No alerts found. All entities are within normal parameters.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
