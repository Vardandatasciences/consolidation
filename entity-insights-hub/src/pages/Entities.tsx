import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, MoreVertical, Building2, Clock, ChevronDown, Loader2 } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from "react";
import { entityApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";

type Entity = {
  ent_id: number;
  ent_name: string;
  ent_code: string;
  lcl_curr: string;
  city?: string;
  country?: string;
  parent_entity_id?: number | null;
  parent_name?: string;
  parent_code?: string;
};

export default function Entities() {
  const { toast } = useToast();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [viewDetailsOpen, setViewDetailsOpen] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [hierarchyData, setHierarchyData] = useState<any>(null);
  const [loadingHierarchy, setLoadingHierarchy] = useState(false);
  const [form, setForm] = useState({
    ent_name: "",
    ent_code: "",
    lcl_curr: "",
    city: "",
    country: "",
    parent_entity_id: "" as string | number,
  });

  const loadEntities = async () => {
    try {
      setIsLoading(true);
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
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadEntities();
  }, []);

  const onCreate = async () => {
    try {
      if (!form.ent_name || !form.ent_code || !form.lcl_curr) {
        toast({
          title: "Missing fields",
          description: "ent_name, ent_code and lcl_curr are required",
          variant: "destructive",
        });
        return;
      }
      const parentId = form.parent_entity_id && form.parent_entity_id !== "" && form.parent_entity_id !== "0" 
        ? (typeof form.parent_entity_id === 'string' ? parseInt(form.parent_entity_id, 10) : form.parent_entity_id)
        : null;
      
      const res = await entityApi.create({
        ent_name: form.ent_name,
        ent_code: form.ent_code,
        lcl_curr: form.lcl_curr,
        city: form.city || undefined,
        country: form.country || undefined,
        parent_entity_id: parentId,
      });
      if (res.success) {
        toast({ title: "Entity created" });
        setOpen(false);
        setForm({ ent_name: "", ent_code: "", lcl_curr: "", city: "", country: "", parent_entity_id: "" });
        loadEntities();
      }
    } catch (e: any) {
      toast({
        title: "Create failed",
        description: e.message || "Unable to create entity",
        variant: "destructive",
      });
    }
  };

  const handleEdit = (entity: Entity) => {
    setSelectedEntity(entity);
    setForm({
      ent_name: entity.ent_name,
      ent_code: entity.ent_code,
      lcl_curr: entity.lcl_curr,
      city: entity.city || "",
      country: entity.country || "",
      parent_entity_id: entity.parent_entity_id || "",
    });
    setEditOpen(true);
  };

  const onUpdate = async () => {
    if (!selectedEntity) return;
    try {
      if (!form.ent_name || !form.ent_code || !form.lcl_curr) {
        toast({
          title: "Missing fields",
          description: "ent_name, ent_code and lcl_curr are required",
          variant: "destructive",
        });
        return;
      }
      const parentId = form.parent_entity_id && form.parent_entity_id !== "" && form.parent_entity_id !== "0"
        ? (typeof form.parent_entity_id === 'string' ? parseInt(form.parent_entity_id, 10) : form.parent_entity_id)
        : null;
      
      const res = await entityApi.update(selectedEntity.ent_id, {
        ent_name: form.ent_name,
        ent_code: form.ent_code,
        lcl_curr: form.lcl_curr,
        city: form.city || undefined,
        country: form.country || undefined,
        parent_entity_id: parentId,
      });
      if (res.success) {
        toast({ title: "Entity updated" });
        setEditOpen(false);
        setSelectedEntity(null);
        setForm({ ent_name: "", ent_code: "", lcl_curr: "", city: "", country: "", parent_entity_id: "" });
        loadEntities();
      }
    } catch (e: any) {
      toast({
        title: "Update failed",
        description: e.message || "Unable to update entity",
        variant: "destructive",
      });
    }
  };

  const handleDelete = (entity: Entity) => {
    setSelectedEntity(entity);
    setDeleteDialogOpen(true);
  };

  const handleViewDetails = async (entity: Entity) => {
    setSelectedEntity(entity);
    setViewDetailsOpen(true);
    setLoadingHierarchy(true);
    try {
      const res = await entityApi.getHierarchy(entity.ent_id);
      if (res.success && res.data) {
        setHierarchyData(res.data);
      }
    } catch (e: any) {
      toast({
        title: "Failed to load hierarchy",
        description: e.message || "Could not fetch entity hierarchy",
        variant: "destructive",
      });
    } finally {
      setLoadingHierarchy(false);
    }
  };

  const onDelete = async () => {
    if (!selectedEntity) return;
    try {
      const res = await entityApi.delete(selectedEntity.ent_id);
      if (res.success) {
        toast({ title: "Entity deleted" });
        setDeleteDialogOpen(false);
        setSelectedEntity(null);
        loadEntities();
      }
    } catch (e: any) {
      toast({
        title: "Delete failed",
        description: e.message || "Unable to delete entity",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="page-shell">
      <div className="toolbar-stack">
        <div>
          <h1 className="page-title text-3xl sm:text-4xl">Entities Management</h1>
          <p className="subtle-text mt-1">Manage your companies and organizations</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 gradient-primary text-white shadow-primary">
              <Plus className="h-4 w-4" />
              Add New Entity
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Add New Entity</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-1 gap-4 py-4">
              <div className="space-y-2">
                <Label>Entity Name</Label>
                <Input value={form.ent_name} onChange={(e) => setForm({ ...form, ent_name: e.target.value })} placeholder="Risk Analytics & Data Solutions INC" />
              </div>
              <div className="space-y-2">
                <Label>Entity Code</Label>
                <Input value={form.ent_code} onChange={(e) => setForm({ ...form, ent_code: e.target.value })} placeholder="RADSINC" />
              </div>
              <div className="space-y-2">
                <Label>Local Currency (3 letters)</Label>
                <Input value={form.lcl_curr} onChange={(e) => setForm({ ...form, lcl_curr: e.target.value.toUpperCase() })} placeholder="AED" maxLength={3} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>City</Label>
                  <Input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder="Dubai" />
                </div>
                <div className="space-y-2">
                  <Label>Country</Label>
                  <Input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} placeholder="UAE" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Parent Entity (Optional)</Label>
                <Select
                  value={form.parent_entity_id?.toString() || "0"}
                  onValueChange={(value) => setForm({ ...form, parent_entity_id: value === "0" ? "" : value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent entity (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">None (Root Entity)</SelectItem>
                    {entities.map((entity) => (
                      <SelectItem key={entity.ent_id} value={entity.ent_id.toString()}>
                        {entity.ent_name} ({entity.ent_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">Leave as "None" to create a root entity</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button className="gradient-primary text-white" onClick={onCreate}>Save</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="card-grid md:grid-cols-3">
        <Card className="border-0 shadow-md card-hover bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Entities</CardTitle>
            <div className="p-2.5 rounded-lg bg-primary-light"><Building2 className="h-5 w-5 text-primary" /></div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{entities.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Active in system</p>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md card-hover bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Entities</CardTitle>
            <div className="p-2.5 rounded-lg bg-success-light"><Building2 className="h-5 w-5 text-success" /></div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{entities.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Assumed active</p>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md card-hover bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Recent Updates</CardTitle>
            <div className="p-2.5 rounded-lg bg-warning-light"><Clock className="h-5 w-5 text-warning" /></div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">—</div>
            <p className="text-xs text-muted-foreground mt-1">Based on upload history</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary-light"><Building2 className="h-5 w-5 text-primary" /></div>
            <CardTitle>All Entities</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="table-responsive">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Code</TableHead>
                <TableHead>Entity Name</TableHead>
                <TableHead>Parent Entity</TableHead>
                <TableHead>Local Currency</TableHead>
                <TableHead>City</TableHead>
                <TableHead>Country</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entities.map((entity) => (
                <TableRow key={entity.ent_id} className="hover:bg-muted/50">
                  <TableCell className="font-medium text-primary">{entity.ent_code}</TableCell>
                  <TableCell className="font-medium">{entity.ent_name}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {entity.parent_name ? (
                      <span>{entity.parent_name} <span className="text-xs">({entity.parent_code})</span></span>
                    ) : (
                      <Badge variant="outline" className="text-xs">Root</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{entity.lcl_curr}</TableCell>
                  <TableCell className="text-muted-foreground">{entity.city || "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{entity.country || "—"}</TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleViewDetails(entity)}>View Details</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleEdit(entity)}>Edit</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleDelete(entity)} className="text-destructive">Delete</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
              {(!entities || entities.length === 0) && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                    {isLoading ? "Loading..." : "No entities found"}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          </div>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Entity</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 gap-4 py-4">
            <div className="space-y-2">
              <Label>Entity Name</Label>
              <Input value={form.ent_name} onChange={(e) => setForm({ ...form, ent_name: e.target.value })} placeholder="Risk Analytics & Data Solutions INC" />
            </div>
            <div className="space-y-2">
              <Label>Entity Code</Label>
              <Input value={form.ent_code} onChange={(e) => setForm({ ...form, ent_code: e.target.value })} placeholder="RADSINC" />
            </div>
            <div className="space-y-2">
              <Label>Local Currency (3 letters)</Label>
              <Input value={form.lcl_curr} onChange={(e) => setForm({ ...form, lcl_curr: e.target.value.toUpperCase() })} placeholder="AED" maxLength={3} />
            </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>City</Label>
                  <Input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder="Dubai" />
                </div>
                <div className="space-y-2">
                  <Label>Country</Label>
                  <Input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} placeholder="UAE" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Parent Entity (Optional)</Label>
                <Select
                  value={form.parent_entity_id?.toString() || "0"}
                  onValueChange={(value) => setForm({ ...form, parent_entity_id: value === "0" ? "" : value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent entity (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">None (Root Entity)</SelectItem>
                    {entities.filter(e => e.ent_id !== selectedEntity?.ent_id).map((entity) => (
                      <SelectItem key={entity.ent_id} value={entity.ent_id.toString()}>
                        {entity.ent_name} ({entity.ent_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">Select "None" to make this a root entity</p>
              </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setEditOpen(false);
              setSelectedEntity(null);
              setForm({ ent_name: "", ent_code: "", lcl_curr: "", city: "", country: "", parent_entity_id: "" });
            }}>Cancel</Button>
            <Button className="gradient-primary text-white" onClick={onUpdate}>Update</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the entity
              <strong> "{selectedEntity?.ent_name}" ({selectedEntity?.ent_code})</strong>.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setDeleteDialogOpen(false);
              setSelectedEntity(null);
            }}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={onDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* View Details Dialog with Tree Structure */}
      <Dialog open={viewDetailsOpen} onOpenChange={setViewDetailsOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>Entity Hierarchy - {selectedEntity?.ent_name}</DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[70vh] pr-4">
          {loadingHierarchy ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="ml-2 text-muted-foreground">Loading hierarchy...</p>
            </div>
          ) : hierarchyData ? (
            <EntityTreeView data={hierarchyData} />
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No hierarchy data available</p>
            </div>
          )}
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setViewDetailsOpen(false);
              setSelectedEntity(null);
              setHierarchyData(null);
            }}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Tree View Component - Horizontal Layout with Curved Connections
function EntityTreeView({ data }: { data: { entity: any; parent: any | null; children: any[]; grandchildren: any[] } }) {
  const { entity, parent, children, grandchildren } = data;
  
  // Build a map of grandchildren by parent_id
  const grandchildrenByParent = new Map<number, any[]>();
  grandchildren.forEach((gc) => {
    const parentId = gc.parent_entity_id;
    if (parentId) {
      if (!grandchildrenByParent.has(parentId)) {
        grandchildrenByParent.set(parentId, []);
      }
      grandchildrenByParent.get(parentId)!.push(gc);
    }
  });

  // Color classes for levels
  const getLevelColor = (level: number) => {
    switch (level) {
      case 0: return "bg-slate-100 border-slate-400";
      case 1: return "bg-green-100 border-green-400";
      case 2: return "bg-yellow-100 border-yellow-400";
      case 3: return "bg-blue-100 border-blue-400";
      default: return "bg-red-100 border-red-400";
    }
  };

  const getLineColor = (level: number) => {
    switch (level) {
      case 1: return "#4ade80"; // green-400
      case 2: return "#facc15"; // yellow-400
      case 3: return "#60a5fa"; // blue-400
      default: return "#f87171"; // red-400
    }
  };

  // Truncate text
  const truncateText = (text: string, maxLength: number = 20) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  return (
    <div className="entity-tree-container p-4 bg-white">
      {/* Parent Entity - Show at top if exists */}
      {parent && (
        <div className="mb-3">
          <div className="text-xs font-medium text-muted-foreground mb-1">Parent:</div>
          <div className="inline-block">
            <div className={`${getLevelColor(0)} border-2 rounded-lg px-2 py-1 min-w-[110px] max-w-[130px] text-center`}>
              <div className="font-semibold text-xs leading-tight">{truncateText(parent.ent_name, 16)}</div>
              <div className="text-xs text-slate-600 mt-0.5">{parent.ent_code}</div>
            </div>
          </div>
        </div>
      )}

      {/* Horizontal Tree Structure - Root → Child → All Grandchildren */}
      <div className="flex items-center gap-3 py-4 overflow-x-auto">
        {/* Root Entity */}
        <div className="flex-shrink-0">
          <div className={`${getLevelColor(0)} border-2 rounded-lg px-2 py-1.5 min-w-[110px] max-w-[130px] text-center`}>
            <div className="flex items-center justify-center gap-1 mb-1">
              <Building2 className="h-3.5 w-3.5 text-slate-700" />
              <ChevronDown className="h-3 w-3 text-slate-600" />
            </div>
            <div className="font-semibold text-xs text-slate-900 leading-tight">{truncateText(entity.ent_name, 18)}</div>
            <div className="text-xs font-medium text-slate-700 mt-0.5">{entity.ent_code}</div>
            <div className="text-xs text-slate-600 mt-0.5">{entity.lcl_curr}</div>
          </div>
        </div>

        {/* Show children and their grandchildren */}
        {children.length > 0 && children.map((child, childIdx) => {
          const childGrandchildren = grandchildrenByParent.get(child.ent_id) || [];
          
          return (
            <div key={child.ent_id} className="flex items-center gap-3">
              {/* Green line from root to child */}
              <div className="flex-shrink-0" style={{ width: '40px', height: '2px', backgroundColor: getLineColor(1) }}></div>

              {/* Child Node */}
              <div className="flex-shrink-0">
                <div className={`${getLevelColor(1)} border-2 rounded-lg px-2 py-1.5 min-w-[110px] max-w-[130px] text-center`}>
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Building2 className="h-3.5 w-3.5 text-green-700" />
                    {childGrandchildren.length > 0 && <ChevronDown className="h-3 w-3 text-green-600" />}
                  </div>
                  <div className="font-semibold text-xs text-green-900 leading-tight">{truncateText(child.ent_name, 18)}</div>
                  <div className="text-xs font-medium text-green-700 mt-0.5">{child.ent_code}</div>
                  <div className="text-xs text-green-600 mt-0.5">{child.lcl_curr}</div>
                </div>
              </div>

              {/* Yellow line from child to grandchildren + All grandchildren */}
              {childGrandchildren.length > 0 && (
                <>
                  <div className="flex-shrink-0" style={{ width: '30px', height: '2px', backgroundColor: getLineColor(2) }}></div>
                  
                  {/* All grandchildren in horizontal row */}
                  {childGrandchildren.map((grandchild, gcIdx) => (
                    <div key={grandchild.ent_id} className="flex items-center gap-3">
                      <div className="flex-shrink-0">
                        <div className={`${getLevelColor(2)} border-2 rounded-lg px-2 py-1 min-w-[100px] max-w-[120px] text-center`}>
                          <div className="flex items-center justify-center gap-1 mb-0.5">
                            <Building2 className="h-3 w-3 text-yellow-700" />
                          </div>
                          <div className="font-medium text-xs text-yellow-900 leading-tight">{truncateText(grandchild.ent_name, 15)}</div>
                          <div className="text-xs text-yellow-700 mt-0.5">{grandchild.ent_code}</div>
                        </div>
                      </div>
                      {/* Line between grandchildren */}
                      {gcIdx < childGrandchildren.length - 1 && (
                        <div className="flex-shrink-0" style={{ width: '20px', height: '2px', backgroundColor: getLineColor(2) }}></div>
                      )}
                    </div>
                  ))}
                </>
              )}

              {/* Line between different children (if multiple children) */}
              {childIdx < children.length - 1 && (
                <div className="flex-shrink-0" style={{ width: '20px', height: '2px', backgroundColor: getLineColor(1) }}></div>
              )}
            </div>
          );
        })}
      </div>

      {/* No children message */}
      {children.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <Building2 className="h-12 w-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium">This entity has no child entities</p>
        </div>
      )}
    </div>
  );
}
