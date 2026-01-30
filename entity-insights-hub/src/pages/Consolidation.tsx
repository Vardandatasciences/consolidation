import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import React from "react";
import { structuredDataApi, entityApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Download } from "lucide-react";

interface Entity {
  ent_id: number;
  ent_name: string;
  ent_code: string;
}

interface ConsolidationData {
  balance_sheet: Record<string, Record<string, Record<number, number>>>;
  profit_loss: Record<string, Record<string, Record<number, number>>>;
  entities: Array<{ ent_id: number; ent_name: string; ent_code: string }>;
}

export default function Consolidation() {
  const { toast } = useToast();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [selectedEntityId, setSelectedEntityId] = useState<number | null>(null);
  const [consolidationData, setConsolidationData] = useState<ConsolidationData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    fetchEntities();
  }, []);

  useEffect(() => {
    if (selectedEntityId) {
      fetchConsolidationData();
    } else {
      setConsolidationData(null);
    }
  }, [selectedEntityId]);

  const fetchEntities = async () => {
    try {
      const response = await entityApi.list();
      if (response.success && response.data?.entities) {
        setEntities(response.data.entities);
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to fetch entities",
        variant: "destructive",
      });
    }
  };

  const fetchConsolidationData = async () => {
    if (!selectedEntityId) return;
    
    setIsLoading(true);
    try {
      const response = await structuredDataApi.getConsolidation(selectedEntityId);
      if (response.success && response.data) {
        setConsolidationData(response.data);
      } else {
        toast({
          title: "Error",
          description: response.message || "Failed to fetch consolidation data",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to fetch consolidation data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatNumber = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return "";
    const num = typeof value === 'number' ? value : parseFloat(String(value));
    if (isNaN(num)) return "";
    
    // Format with commas and handle negative numbers with parentheses
    const absValue = Math.abs(num);
    const formatted = absValue.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    
    return num < 0 ? `(${formatted})` : formatted;
  };

  // Calculate horizontal total for a row (sum of all entity values in that row)
  const calculateRowTotal = (
    rowData: Record<number, number>,
    entityIds: number[]
  ): number => {
    let total = 0;
    entityIds.forEach((entityId) => {
      total += rowData[entityId] || 0;
    });
    return total;
  };

  // Calculate vertical total for a column (sum of all values in that entity column)
  const calculateColumnTotal = (
    data: Record<string, Record<string, Record<number, number>>>,
    entityId: number
  ): number => {
    let total = 0;
    Object.values(data).forEach((category1Data) => {
      Object.values(category1Data).forEach((category2Data) => {
        total += category2Data[entityId] || 0;
      });
    });
    return total;
  };

  // Calculate grand total (sum of all values in the entire section)
  const calculateGrandTotal = (
    data: Record<string, Record<string, Record<number, number>>>,
    entityIds: number[]
  ): number => {
    let total = 0;
    Object.values(data).forEach((category1Data) => {
      Object.values(category1Data).forEach((category2Data) => {
        entityIds.forEach((entityId) => {
          total += category2Data[entityId] || 0;
        });
      });
    });
    return total;
  };

  // Calculate Category 1 total (sum of all Category 2 values under it)
  const calculateCategory1Total = (
    category1Data: Record<string, Record<number, number>>,
    entityIds: number[]
  ): number => {
    let total = 0;
    Object.values(category1Data).forEach((category2Data) => {
      entityIds.forEach((entityId) => {
        total += category2Data[entityId] || 0;
      });
    });
    return total;
  };

  const renderSection = (
    title: string,
    data: Record<string, Record<string, Record<number, number>>>,
    entityList: Array<{ ent_id: number; ent_name: string; ent_code: string }>,
    returnColumnTotals?: boolean,
    overallGrandTotalRow?: { columnTotals: Record<number, number>; grandTotal: number }
  ): { component: JSX.Element | null; columnTotals?: Record<number, number> } => {
    if (!data || Object.keys(data).length === 0) {
      return { component: null };
    }

    const entityIds = entityList.map((e) => e.ent_id);
    const grandTotal = calculateGrandTotal(data, entityIds);
    
    // Calculate column totals for each entity
    const columnTotals: Record<number, number> = {};
    entityIds.forEach((entityId) => {
      columnTotals[entityId] = calculateColumnTotal(data, entityId);
    });

    const component = (
      <Card className="mb-6 w-full">
        <CardHeader>
          <CardTitle className="text-xl font-bold">{title}</CardTitle>
        </CardHeader>
        <CardContent className="p-4 w-full" style={{ overflowX: 'hidden', maxWidth: '100%' }}>
          <div className="w-full" style={{ overflowX: 'hidden', maxWidth: '100%' }}>
            <Table className="w-full table-auto" style={{ tableLayout: 'auto', width: '100%' }}>
              <TableHeader>
                <TableRow>
                  <TableHead className="font-bold w-[180px]">Row Labels</TableHead>
                  {entityList.map((entity) => (
                    <TableHead key={entity.ent_id} className="text-right font-bold text-[10px] px-1 w-auto">
                      <div className="break-words leading-tight" title={entity.ent_name}>
                        {entity.ent_name.length > 20 ? `${entity.ent_name.substring(0, 20)}...` : entity.ent_name}
                      </div>
                    </TableHead>
                  ))}
                  <TableHead className="text-right font-bold text-xs px-2 w-[100px]">Grand Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(data).map(([category1, category1Data]) => {
                  // Calculate Category 1 row total (sum of all Category 2 values horizontally)
                  const category1RowData: Record<number, number> = {};
                  entityIds.forEach((entityId) => {
                    category1RowData[entityId] = Object.values(category1Data).reduce(
                      (sum, category2Data) => sum + (category2Data[entityId] || 0),
                      0
                    );
                  });
                  const category1RowTotal = calculateRowTotal(category1RowData, entityIds);
                  
                  const hasCategory2 = Object.keys(category1Data).some(
                    (key) => key && key.trim() !== ""
                  );

                  return (
                    <React.Fragment key={category1}>
                      {/* Category 1 Header */}
                      <TableRow className="bg-muted/50">
                        <TableCell className="font-bold w-[180px]">{category1 || "(blank)"}</TableCell>
                        {entityIds.map((entityId) => (
                          <TableCell key={entityId} className="text-right font-bold text-[10px] px-1">
                            {formatNumber(category1RowData[entityId])}
                          </TableCell>
                        ))}
                        <TableCell className="text-right font-bold text-xs px-2">
                          {formatNumber(category1RowTotal)}
                        </TableCell>
                      </TableRow>

                      {/* Category 2 rows */}
                      {hasCategory2 &&
                        Object.entries(category1Data).map(([category2, category2Data]) => {
                          const category2RowTotal = calculateRowTotal(category2Data, entityIds);
                          return (
                            <TableRow key={`${category1}-${category2}`} className="bg-background">
                              <TableCell className="pl-8 w-[180px]">{category2 || "(blank)"}</TableCell>
                              {entityIds.map((entityId) => (
                                <TableCell key={entityId} className="text-right text-[10px] px-1">
                                  {formatNumber(category2Data[entityId])}
                                </TableCell>
                              ))}
                              <TableCell className="text-right text-xs px-2">
                                {formatNumber(category2RowTotal)}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                    </React.Fragment>
                  );
                })}
                {/* Grand Total Row (Bottom) - Vertical totals for each column */}
                <TableRow className="bg-muted font-bold border-t-2">
                  <TableCell className="font-bold w-[180px]">Grand Total</TableCell>
                  {entityIds.map((entityId) => (
                    <TableCell key={entityId} className="text-right font-bold text-[10px] px-1">
                      {formatNumber(columnTotals[entityId])}
                    </TableCell>
                  ))}
                  <TableCell className="text-right font-bold text-xs px-2">
                    {formatNumber(grandTotal)}
                  </TableCell>
                </TableRow>
                {/* Overall Grand Total Row (only for Profit & Loss section) */}
                {overallGrandTotalRow && (
                  <TableRow className="bg-muted/70 font-bold border-t-2">
                    <TableCell className="font-bold w-[180px]">Grand Total</TableCell>
                    {entityIds.map((entityId) => (
                      <TableCell key={entityId} className="text-right font-bold text-[10px] px-1">
                        {formatNumber(overallGrandTotalRow.columnTotals[entityId])}
                      </TableCell>
                    ))}
                    <TableCell className="text-right font-bold text-xs px-2">
                      {formatNumber(overallGrandTotalRow.grandTotal)}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    );
    
    return { component, columnTotals: returnColumnTotals ? columnTotals : undefined };
  };

  const handleExportToExcel = async () => {
    if (!selectedEntityId) {
      toast({
        title: "No entity selected",
        description: "Please select an entity before exporting.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsExporting(true);
      
      // Call the export API
      const blob = await structuredDataApi.exportConsolidationToExcel(selectedEntityId);
      
      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `consolidation_export_${timestamp}.xlsx`;
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

  return (
    <div className="w-full p-6 space-y-6" style={{ maxWidth: '100%', overflowX: 'hidden' }}>
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Consolidation</h1>
        {selectedEntityId && (
          <Button
            onClick={handleExportToExcel}
            disabled={isExporting}
            className="flex items-center gap-2"
          >
            {isExporting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Export to Excel
              </>
            )}
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select Entity</CardTitle>
        </CardHeader>
        <CardContent>
          <Select
            value={selectedEntityId?.toString() || ""}
            onValueChange={(value) => setSelectedEntityId(value ? parseInt(value) : null)}
          >
            <SelectTrigger className="w-full max-w-md">
              <SelectValue placeholder="Select an entity" />
            </SelectTrigger>
            <SelectContent>
              {entities.map((entity) => (
                <SelectItem key={entity.ent_id} value={entity.ent_id.toString()}>
                  {entity.ent_name} ({entity.ent_code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {!isLoading && consolidationData && (() => {
        const entityIds = consolidationData.entities.map((e) => e.ent_id);
        
        // Render Balance Sheet section and get its column totals
        const balanceSheetResult = renderSection(
          "Balance Sheet",
          consolidationData.balance_sheet,
          consolidationData.entities,
          true
        );
        
        // Calculate overall grand total (sum of Balance Sheet + Profit & Loss for each column)
        const overallColumnTotals: Record<number, number> = {};
        let overallGrandTotal = 0;
        
        entityIds.forEach((entityId) => {
          const bsTotal = balanceSheetResult.columnTotals?.[entityId] || 0;
          // We'll calculate PL total after rendering, but we need to pre-calculate for the overall total
          // So we'll calculate it here first
          const plColumnTotal = calculateColumnTotal(consolidationData.profit_loss, entityId);
          overallColumnTotals[entityId] = bsTotal + plColumnTotal;
          overallGrandTotal += overallColumnTotals[entityId];
        });
        
        // Render Profit & Loss section with overall grand total row
        const profitLossResult = renderSection(
          "Profit & Loss",
          consolidationData.profit_loss,
          consolidationData.entities,
          true,
          {
            columnTotals: overallColumnTotals,
            grandTotal: overallGrandTotal
          }
        );
        
        return (
          <div className="space-y-6">
            {/* Balance Sheet Section */}
            {balanceSheetResult.component}

            {/* Profit & Loss Section (includes overall grand total row) */}
            {profitLossResult.component}
          </div>
        );
      })()}

      {!isLoading && !consolidationData && selectedEntityId && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No consolidation data available for the selected entity.
          </CardContent>
        </Card>
      )}
    </div>
  );
}

