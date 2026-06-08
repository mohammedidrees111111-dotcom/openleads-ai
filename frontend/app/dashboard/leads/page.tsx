"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { leadsAPI } from "@/lib/api";
import { formatDate, getStatusColor } from "@/lib/utils";
import { Plus, Search, RefreshCw, Download, Filter, X, Loader2, Trash2, Edit3 } from "lucide-react";

const MODAL_STYLE = "fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm";

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDetailId, setShowDetailId] = useState<number | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [newLead, setNewLead] = useState({ name: "", email: "", company: "", website: "", phone: "" });
  const [saving, setSaving] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  useEffect(() => { loadLeads(); }, [page, statusFilter]);

  const loadLeads = async () => {
    setLoading(true); setError("");
    try {
      const res = await leadsAPI.list({ page, per_page: 20, search, status: statusFilter || undefined });
      setLeads(res.data.items);
      setTotal(res.data.total);
    } catch (err) { setError("Failed to load leads"); }
    finally { setLoading(false); }
  };

  const handleExport = () => {
    const csv = ["Name,Company,Email,Status,Score,Source,Date"];
    leads.forEach(l => csv.push(`"${l.name}","${l.company}","${l.email}","${l.status}",${l.score},"${l.source}","${l.created_at}"`));
    const blob = new Blob([csv.join("\n")], { type: "text/csv" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "leads.csv"; a.click();
  };

  const handleAddLead = async () => {
    if (!newLead.name) return;
    setSaving(true); setError("");
    try {
      await leadsAPI.create(newLead);
      setShowAddModal(false);
      setNewLead({ name: "", email: "", company: "", website: "", phone: "" });
      loadLeads();
    } catch (err) { setError("Failed to create lead"); }
    finally { setSaving(false); }
  };

  const handleUpdateLead = async () => {
    if (!detail || !detail.name) return;
    setSaving(true);
    try {
      await leadsAPI.update(detail.id, { name: detail.name, email: detail.email, company: detail.company, website: detail.website, phone: detail.phone });
      setShowDetailId(null); setDetail(null); loadLeads();
    } catch (err) { setDetailError("Failed to update lead"); }
    finally { setSaving(false); }
  };

  const handleDeleteLead = async (id: number) => {
    if (!confirm("Delete this lead?")) return;
    try {
      await leadsAPI.delete(id);
      loadLeads();
    } catch (err) { setError("Failed to delete lead"); }
  };

  const handleViewDetail = async (id: number) => {
    setShowDetailId(id); setDetailError("");
    try {
      const res = await leadsAPI.get(id);
      setDetail(res.data);
    } catch (err) { setDetailError("Failed to load lead details"); }
  };

  const handleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleBulkExport = () => {
    if (selectedIds.size === 0) { handleExport(); return; }
    const csv = ["Name,Company,Email,Status,Score,Source,Date"];
    leads.filter(l => selectedIds.has(l.id)).forEach(l =>
      csv.push(`"${l.name}","${l.company}","${l.email}","${l.status}",${l.score},"${l.source}","${l.created_at}"`)
    );
    const blob = new Blob([csv.join("\n")], { type: "text/csv" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "selected-leads.csv"; a.click();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Leads</h1>
          <p className="text-muted-foreground">{total} total leads in your pipeline</p>
        </div>
      {error && <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">{error}</div>}

      <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="gap-2" onClick={() => setStatusFilter(statusFilter ? "" : "new")}>
            <Filter className="h-4 w-4" /> {statusFilter ? `Status: ${statusFilter}` : "Filter"}
          </Button>
          <Button variant="outline" size="sm" className="gap-2" onClick={handleBulkExport}>
            <Download className="h-4 w-4" /> Export
          </Button>
          <Button size="sm" className="gap-2" onClick={() => setShowAddModal(true)}>
            <Plus className="h-4 w-4" /> Add Lead
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search leads..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" onKeyDown={(e) => e.key === "Enter" && loadLeads()} />
        </div>
        <Button variant="ghost" size="icon" onClick={loadLeads}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
        {selectedIds.size > 0 && (
          <span className="text-sm text-muted-foreground">{selectedIds.size} selected</span>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="w-10 p-4"><input type="checkbox" onChange={(e) => { if (e.target.checked) setSelectedIds(new Set(leads.map(l => l.id))); else setSelectedIds(new Set()); }} checked={selectedIds.size === leads.length && leads.length > 0} /></th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Name</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Company</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Email</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Status</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Score</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Source</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Date</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={9} className="text-center py-12 text-muted-foreground">Loading...</td></tr>
                ) : leads.length === 0 ? (
                  <tr><td colSpan={9} className="text-center py-12 text-muted-foreground">No leads found. Start by searching for leads!</td></tr>
                ) : (
                  leads.map((lead) => (
                    <tr key={lead.id} className="border-b last:border-0 hover:bg-accent/50 transition-colors">
                      <td className="p-4"><input type="checkbox" checked={selectedIds.has(lead.id)} onChange={() => handleSelect(lead.id)} /></td>
                      <td className="p-4"><p className="font-medium">{lead.name}</p></td>
                      <td className="p-4 text-sm">{lead.company || "-"}</td>
                      <td className="p-4 text-sm text-muted-foreground">{lead.email || "-"}</td>
                      <td className="p-4"><Badge variant="outline" className={getStatusColor(lead.status)}>{lead.status}</Badge></td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-16 rounded-full bg-secondary overflow-hidden">
                            <div className={`h-full rounded-full ${lead.score >= 70 ? "bg-green-500" : lead.score >= 40 ? "bg-yellow-500" : "bg-red-500"}`} style={{ width: `${lead.score}%` }} />
                          </div>
                          <span className="text-sm font-medium">{lead.score}</span>
                        </div>
                      </td>
                      <td className="p-4 text-sm text-muted-foreground">{lead.source}</td>
                      <td className="p-4 text-sm text-muted-foreground">{formatDate(lead.created_at)}</td>
                      <td className="p-4 text-right">
                        <div className="flex items-center gap-1 justify-end">
                          <Button variant="ghost" size="sm" onClick={() => handleViewDetail(lead.id)}>View</Button>
                          <Button variant="ghost" size="sm" onClick={() => handleViewDetail(lead.id)}><Edit3 className="h-3 w-3" /></Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDeleteLead(lead.id)}><Trash2 className="h-3 w-3 text-red-400" /></Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Page {page} of {Math.max(1, Math.ceil(total / 20))}</p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Previous</Button>
          <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 20)}>Next</Button>
        </div>
      </div>

      {showAddModal && (
        <div className={MODAL_STYLE} onClick={() => setShowAddModal(false)}>
          <Card className="w-full max-w-md" onClick={e => e.stopPropagation()}>
            <CardHeader><CardTitle>Add New Lead</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <Input placeholder="Name *" value={newLead.name} onChange={e => setNewLead({...newLead, name: e.target.value})} />
              <Input placeholder="Email" value={newLead.email} onChange={e => setNewLead({...newLead, email: e.target.value})} />
              <Input placeholder="Company" value={newLead.company} onChange={e => setNewLead({...newLead, company: e.target.value})} />
              <Input placeholder="Website" value={newLead.website} onChange={e => setNewLead({...newLead, website: e.target.value})} />
              <Input placeholder="Phone" value={newLead.phone} onChange={e => setNewLead({...newLead, phone: e.target.value})} />
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button onClick={handleAddLead} disabled={saving || !newLead.name}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {showDetailId && detail && (
        <div className={MODAL_STYLE} onClick={() => { setShowDetailId(null); setDetail(null); }}>
          <Card className="w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Edit Lead</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => { setShowDetailId(null); setDetail(null); }}><X className="h-4 w-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><p className="text-xs text-muted-foreground">Name</p><Input value={detail.name} onChange={e => setDetail({...detail, name: e.target.value})} /></div>
                <div><p className="text-xs text-muted-foreground">Email</p><Input value={detail.email || ""} onChange={e => setDetail({...detail, email: e.target.value})} /></div>
                <div><p className="text-xs text-muted-foreground">Company</p><Input value={detail.company || ""} onChange={e => setDetail({...detail, company: e.target.value})} /></div>
                <div><p className="text-xs text-muted-foreground">Phone</p><Input value={detail.phone || ""} onChange={e => setDetail({...detail, phone: e.target.value})} /></div>
                <div><p className="text-xs text-muted-foreground">Website</p><Input value={detail.website || ""} onChange={e => setDetail({...detail, website: e.target.value})} /></div>
                <div><p className="text-xs text-muted-foreground">Industry</p><p className="font-medium">{detail.industry || "-"}</p></div>
                <div><p className="text-xs text-muted-foreground">Location</p><p className="font-medium">{detail.location || "-"}</p></div>
                <div><p className="text-xs text-muted-foreground">Score</p><p className="font-medium">{detail.score}</p></div>
              </div>
              <div className="flex items-center gap-2"><span className="text-xs text-muted-foreground">Status:</span><Badge variant="outline" className={getStatusColor(detail.status)}>{detail.status}</Badge></div>
              {detail.pain_points?.length > 0 && (
                <div><p className="text-xs text-muted-foreground mb-1">Pain Points</p><div className="flex flex-wrap gap-1">{detail.pain_points.map((p: string, i: number) => <Badge key={i} variant="secondary">{p}</Badge>)}</div></div>
              )}
              {detailError && <p className="text-sm text-red-400">{detailError}</p>}
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => { setShowDetailId(null); setDetail(null); }}>Cancel</Button>
                <Button onClick={handleUpdateLead} disabled={saving}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Changes"}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
