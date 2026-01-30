import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Building2, TrendingUp, DollarSign, FileText, RefreshCcw, PieChart as PieChartIcon, LineChart as LineChartIcon } from "lucide-react";
import { dashboardApi, uploadApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  Area,
  AreaChart,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

type Entity = { ent_id: number; ent_name: string; ent_code: string };

type DashboardOverview = {
  kpis: {
    total_entities: number;
    total_records: number;
    total_amount: number;
    total_amount_usd: number;
    latest_year: number | null;
    mapped_count: number;
    unmapped_count: number;
    mapped_ratio: number;
    fx_coverage_ratio: number;
    code_master_count: number;
  };
  category_breakdown: { category: string; total_amount: number }[];
  subcategory_breakdown: { sub_category: string; total_amount: number }[];
  entity_totals: { entity_name: string; entity_code: string; total_amount: number }[];
  yearly_trend: { year: number; total_amount: number }[];
  monthly_trend: { year: number; month: string; total_amount: number }[];
  top_accounts: {
    account_name: string;
    mainCategory: string;
    category1: string;
    category2: string;
    total_amount: number;
  }[];
  bottom_accounts: {
    account_name: string;
    mainCategory: string;
    category1: string;
    category2: string;
    total_amount: number;
  }[];
  currency_mix: { currency: string; total_amount: number }[];
  fx_gaps: { currency: string; missing_fx_rows: number }[];
  unmapped: { account_name: string; total_amount: number }[];
  pl_bs_mix: { bucket: string; total_amount: number }[];
  concentration: { top5: any[]; others_total: number };
  variance_year: { year: number; total_amount: number; delta_amount: number; delta_percent: number }[];
  variance_month: { label: string; total_amount: number; delta_amount: number; delta_percent: number }[];
  alerts: string[];
};

const PIE_COLORS = ["#2563eb", "#22c55e", "#f59e0b", "#06b6d4", "#a855f7", "#ef4444", "#0ea5e9", "#10b981"];

const formatCurrency = (val: number) => {
  if (!val) return "₹0";
  const abs = Math.abs(val);
  if (abs >= 1_00_00_000) return `₹${(val / 1_00_00_000).toFixed(1)} Cr`;
  if (abs >= 1_00_000) return `₹${(val / 1_00_000).toFixed(1)} L`;
  return `₹${val.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
};

const formatPercent = (val: number | string) => {
  const num = typeof val === "string" ? parseFloat(val) : val;
  const safe = Number.isFinite(num) ? num : 0;
  return `${safe.toFixed(1)}%`;
};

const hasData = (rows: any[] | undefined, key: string) => {
  if (!rows || rows.length === 0) return false;
  return rows.some((r) => {
    const v = r?.[key];
    return typeof v === "number" ? v !== 0 : !!v;
  });
};

export default function Dashboard() {
  const { toast } = useToast();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [years, setYears] = useState<number[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<string>("all");
  const [selectedYear, setSelectedYear] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const loadFilters = async () => {
      try {
        const [entRes, yearsRes] = await Promise.all([uploadApi.getEntities(), uploadApi.getFinancialYears()]);
        if (entRes.success && entRes.data?.entities) setEntities(entRes.data.entities);
        if (yearsRes.success && yearsRes.data?.years) setYears(yearsRes.data.years);
      } catch (error: any) {
        toast({ title: "Failed to load filters", description: error.message, variant: "destructive" });
      }
    };
    loadFilters();
  }, [toast]);

  useEffect(() => {
    fetchOverview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEntity, selectedYear]);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const entityId = selectedEntity !== "all" ? parseInt(selectedEntity) : undefined;
      const year = selectedYear !== "all" ? parseInt(selectedYear) : undefined;
      const res = await dashboardApi.getOverview(entityId, year);
      if (res.success && res.data) {
        setOverview(res.data as DashboardOverview);
      }
    } catch (error: any) {
      toast({ title: "Failed to load dashboard", description: error.message, variant: "destructive" });
      setOverview(null);
    } finally {
      setLoading(false);
    }
  };

  const kpiCards = useMemo(() => {
    if (!overview) return [];
    return [
      {
        title: "Total Entities",
        value: overview.kpis.total_entities || 0,
        icon: Building2,
        sub: `${overview.kpis.code_master_count || 0} code master rows`,
        color: "bg-primary-light text-primary",
      },
      {
        title: "Total Records",
        value: overview.kpis.total_records || 0,
        icon: FileText,
        sub: overview.kpis.latest_year ? `Latest Year: ${overview.kpis.latest_year}` : "Latest Year: N/A",
        color: "bg-info-light text-info",
      },
      {
        title: "Total Amount",
        value: formatCurrency(overview.kpis.total_amount || 0),
        icon: DollarSign,
        sub: `USD: ${formatCurrency(overview.kpis.total_amount_usd || 0)}`,
        color: "bg-success-light text-success",
      },
      {
        title: "Coverage",
        value: formatPercent(overview.kpis.mapped_ratio || 0),
        icon: PieChartIcon,
        // sub: `FX ready: ${formatPercent(overview.kpis.fx_coverage_ratio || 0)}`,
        color: "bg-accent-light text-accent",
      },
    ];
  }, [overview]);

  const categoryData = overview?.category_breakdown || [];
  const entityData = overview?.entity_totals || [];
  const yearlyTrend = overview?.yearly_trend || [];
  const monthlyTrend = overview?.monthly_trend || [];
  const topAccounts = overview?.top_accounts || [];
  const bottomAccounts = overview?.bottom_accounts || [];
  const currencyMix = overview?.currency_mix || [];
  const plBsMix = overview?.pl_bs_mix || [];
  const varianceYear = overview?.variance_year || [];
  const varianceMonth = overview?.variance_month || [];
  const fxGaps = overview?.fx_gaps || [];
  const unmapped = overview?.unmapped || [];
  const alerts = overview?.alerts || [];
  const concentration = overview?.concentration || { top5: [], others_total: 0 };

  const tooltipStyle = {
    backgroundColor: "rgba(15,23,42,0.92)",
    border: "1px solid #1e293b",
    borderRadius: 12,
    color: "#e2e8f0",
    padding: "10px 12px",
    boxShadow: "0 12px 40px rgba(0,0,0,0.35)",
  } as const;

  return (
    <div className="page-shell">
      <div className="toolbar-stack">
        <div>
          <h1 className="page-title text-3xl sm:text-4xl">Dashboard</h1>
          <p className="subtle-text mt-1">Live insights powered by your structured data</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <Select value={selectedEntity} onValueChange={setSelectedEntity}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select Entity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Entities</SelectItem>
              {entities.map((ent) => (
                <SelectItem key={ent.ent_id} value={String(ent.ent_id)}>
                  {ent.ent_name} ({ent.ent_code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Year" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Years</SelectItem>
              {years.map((yr) => (
                <SelectItem key={yr} value={String(yr)}>
                  {yr}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" className="gap-2" onClick={fetchOverview} disabled={loading}>
            <RefreshCcw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="card-grid md:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((kpi) => (
          <Card key={kpi.title} className="card-hover border-0 shadow-md bg-gradient-to-br from-card to-card/50">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{kpi.title}</CardTitle>
              <div className={`p-2.5 rounded-lg ${kpi.color}`}>
                <kpi.icon className="h-5 w-5" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{kpi.value}</div>
              <p className="text-xs text-muted-foreground mt-1">{kpi.sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="card-grid lg:grid-cols-2">
        <Card className="border-0 shadow-md card-hover chart-surface">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary-light">
                <Building2 className="h-5 w-5 text-primary" />
              </div>
              Entity-wise Totals
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={entityData}>
                <CartesianGrid className="chart-grid" />
                <XAxis dataKey="entity_name" tick={{ fontSize: 10 }} className="chart-axis" />
                <YAxis tickFormatter={(v) => `${Math.round(v / 1_00_000)}L`} className="chart-axis" />
                <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
                <Bar dataKey="total_amount" fill="#2563eb" radius={[8, 8, 8, 8]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-md card-hover chart-surface">
          <CardHeader className="border-b bg-gradient-to-r from-accent/5 to-transparent">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-accent-light">
                <LineChartIcon className="h-5 w-5 text-accent" />
              </div>
              Year-on-Year Trend
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={yearlyTrend}>
                <CartesianGrid className="chart-grid" />
                <XAxis dataKey="year" className="chart-axis" />
                <YAxis tickFormatter={(v) => `${Math.round(v / 1_00_000)}L`} className="chart-axis" />
                <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="total_amount" stroke="#10b981" strokeWidth={3} dot={{ r: 4, strokeWidth: 2, fill: "#ecfeff", stroke: "#10b981" }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card className="border-0 shadow-md card-hover chart-surface">
        <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary-light">
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            Monthly Run-Rate
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={monthlyTrend}>
              <defs>
                <linearGradient id="colorAmt" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid className="chart-grid" />
              <XAxis dataKey="month" />
              <YAxis tickFormatter={(v) => `${Math.round(v / 1_00_000)}L`} />
              <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="total_amount" stroke="#2563eb" strokeWidth={2.5} fill="url(#colorAmt)" />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="card-grid lg:grid-cols-2">
        <Card className="border-0 shadow-md card-hover chart-surface">
          <CardHeader className="border-b bg-gradient-to-r from-accent/5 to-transparent">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-accent-light">
                <PieChartIcon className="h-5 w-5 text-accent" />
              </div>
              Category Mix
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[380px] p-6">
            {hasData(categoryData, "total_amount") ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={categoryData} dataKey="total_amount" nameKey="category" cx="50%" cy="50%" outerRadius={120} innerRadius={60} labelLine={false} label>
                    {categoryData.map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend className="chart-legend" />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No data for selected filters.</div>
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-md card-hover chart-surface">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary-light">
                <PieChartIcon className="h-5 w-5 text-primary" />
              </div>
              P&L vs Balance Sheet
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[380px] p-6">
            {hasData(plBsMix, "total_amount") ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={plBsMix} dataKey="total_amount" nameKey="bucket" cx="50%" cy="50%" outerRadius={120} innerRadius={60} labelLine={false} label>
                    {plBsMix.map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend className="chart-legend" />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No data for selected filters.</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="card-grid lg:grid-cols-2">
        <Card className="border-0 shadow-md card-hover chart-surface">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary-light">
                <DollarSign className="h-5 w-5 text-primary" />
              </div>
              Currency Mix
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[380px] p-6">
            {hasData(currencyMix, "total_amount") ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={currencyMix} dataKey="total_amount" nameKey="currency" cx="50%" cy="50%" outerRadius={120} innerRadius={60} labelLine={false} label>
                    {currencyMix.map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend className="chart-legend" />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No data for selected filters.</div>
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-md card-hover chart-surface">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary-light">
                <PieChartIcon className="h-5 w-5 text-primary" />
              </div>
              Concentration (Top 5)
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[380px] p-6">
            {hasData(concentration?.top5, "total_amount") || (concentration?.others_total || 0) !== 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      ...(concentration?.top5 || []).map((r, idx) => ({
                        name: r.account_name || `Account ${idx + 1}`,
                        value: r.total_amount || 0,
                      })),
                      { name: "Others", value: concentration?.others_total || 0 },
                    ]}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={120}
                    innerRadius={60}
                    labelLine={false}
                    label
                  >
                    {((concentration?.top5 || []).length + 1 > 0
                      ? [...Array((concentration?.top5 || []).length + 1).keys()]
                      : []
                    ).map((idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend className="chart-legend" />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No concentration data.</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="card-grid lg:grid-cols-2">
        <Card className="border-0 shadow-md card-hover chart-surface">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary-light">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              YoY Variance
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[320px] p-4">
            {hasData(varianceYear, "total_amount") ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={varianceYear}>
                  <CartesianGrid className="chart-grid" />
                  <XAxis dataKey="year" className="chart-axis" />
                  <YAxis tickFormatter={(v) => `${Math.round(v / 1_00_000)}L`} className="chart-axis" />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
                  <Bar dataKey="total_amount" fill="#2563eb" radius={[8, 8, 8, 8]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No YoY variance data.</div>
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-md card-hover chart-surface">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary-light">
                <LineChartIcon className="h-5 w-5 text-primary" />
              </div>
              MoM Variance
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[320px] p-4">
            {hasData(varianceMonth, "total_amount") ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={varianceMonth}>
                  <CartesianGrid className="chart-grid" />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                  <YAxis tickFormatter={(v) => `${Math.round(v / 1_00_000)}L`} />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={tooltipStyle} />
                  <Line type="monotone" dataKey="total_amount" stroke="#16a34a" strokeWidth={3} dot={{ r: 4, strokeWidth: 2, fill: "#f0fdf4", stroke: "#16a34a" }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">No MoM variance data.</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary-light">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              Top Accounts (by Particular)
            </CardTitle>
            {overview && (
              <Badge variant="outline" className="text-xs">
                {overview.kpis.mapped_count} mapped / {overview.kpis.unmapped_count} unmapped
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="table-responsive">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Particular</TableHead>
                  <TableHead>Standardized Code</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Sub Category</TableHead>
                  <TableHead className="text-right">Total Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {topAccounts.map((row, idx) => (
                  <TableRow key={`${row.account_name}-${idx}`} className="hover:bg-muted/50">
                    <TableCell className="font-medium">{row.account_name}</TableCell>
                    <TableCell className="text-primary">{row.mainCategory || "—"}</TableCell>
                    <TableCell>{row.category1 || "—"}</TableCell>
                    <TableCell>{row.category2 || "—"}</TableCell>
                    <TableCell className="text-right text-muted-foreground">{formatCurrency(row.total_amount || 0)}</TableCell>
                  </TableRow>
                ))}
                {(!topAccounts || topAccounts.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                      {loading ? "Loading..." : "No data available for selected filters"}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <div className="card-grid lg:grid-cols-2">
        <Card className="border-0 shadow-md">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle>Bottom Accounts (by Particular)</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="table-responsive">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Particular</TableHead>
                    <TableHead>Standardized Code</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Sub Category</TableHead>
                    <TableHead className="text-right">Total Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bottomAccounts.map((row, idx) => (
                    <TableRow key={`${row.account_name}-${idx}`} className="hover:bg-muted/50">
                      <TableCell className="font-medium">{row.account_name}</TableCell>
                      <TableCell className="text-primary">{row.standardizedCode || "—"}</TableCell>
                      <TableCell>{row.categoty1 || "—"}</TableCell>
                      <TableCell>{row.categoty2 || "—"}</TableCell>
                      <TableCell className="text-right text-muted-foreground">{formatCurrency(row.total_amount || 0)}</TableCell>
                    </TableRow>
                  ))}
                  {(!bottomAccounts || bottomAccounts.length === 0) && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                        {loading ? "Loading..." : "No data available for selected filters"}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-md">
          <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
            <CardTitle>Data Quality & Alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Alerts</p>
              {alerts && alerts.length > 0 ? (
                <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                  {alerts.map((a, idx) => (
                    <li key={idx}>{a}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No alerts for current filters.</p>
              )}
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">FX Gaps</p>
              <div className="table-responsive">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead>Currency</TableHead>
                      <TableHead className="text-right">Missing Avg_Fx_Rt</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fxGaps.map((row, idx) => (
                      <TableRow key={idx} className="hover:bg-muted/50">
                        <TableCell>{row.currency}</TableCell>
                        <TableCell className="text-right">{row.missing_fx_rows}</TableCell>
                      </TableRow>
                    ))}
                    {(!fxGaps || fxGaps.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={2} className="text-center text-muted-foreground py-6">
                          No FX gaps.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Unmapped Particulars</p>
              <div className="table-responsive">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead>Particular</TableHead>
                      <TableHead className="text-right">Total Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {unmapped.map((row, idx) => (
                      <TableRow key={idx} className="hover:bg-muted/50">
                        <TableCell className="font-medium">{row.account_name}</TableCell>
                        <TableCell className="text-right text-muted-foreground">{formatCurrency(row.total_amount || 0)}</TableCell>
                      </TableRow>
                    ))}
                    {(!unmapped || unmapped.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={2} className="text-center text-muted-foreground py-6">
                          All mapped.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
