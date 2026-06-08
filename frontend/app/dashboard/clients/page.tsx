"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { clientsAPI } from "@/lib/api";
import { formatCurrency, formatDate, getStatusColor } from "@/lib/utils";
import { Plus, Building2, DollarSign, X, Loader2, Edit3, Trash2 } from "lucide-react";

const MODAL_STYLE = "fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm";

export default function ClientsPage() {
  const [clients, setClients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showEdit, setShowEdit] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", company: "", monthly_price: "" });
  const [error, setError] = useState("");

  useEffect(() => { loadClients(); }, []);

  const loadClients = async () => {
    setError("");
    try { const res = await clientsAPI.list({ per_page: 50 }); setClients(res.data.items); }
    catch (err) { setError("Failed to load clients"); }
    finally { setLoading(false); }
  };

  const handleAdd = async () => {
    if (!form.name || !form.email) return;
    setSaving(true); setError("");
    try {
      await clientsAPI.create({ ...form, monthly_price: parseFloat(form.monthly_price) || 0 });
      setShowAdd(false); setForm({ name: "", email: "", company: "", monthly_price: "" }); loadClients();
    } catch (err) { setError("Failed to add client"); }
    finally { setSaving(false); }
  };

  const handleUpdate = async () => {
    if (!showEdit || !form.name) return;
    setSaving(true); setError("");
    try {
      await clientsAPI.update(showEdit.id, { ...form, monthly_price: parseFloat(form.monthly_price) || 0 });
      setShowEdit(null); setForm({ name: "", email: "", company: "", monthly_price: "" }); loadClients();
    } catch (err) { setError("Failed to update client"); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this client?")) return;
    try { await clientsAPI.delete(id); loadClients(); }
    catch (err) { setError("Failed to delete client"); }
  };

  const openEdit = (client: any) => {
    setShowEdit(client);
    setForm({ name: client.name, email: client.email, company: client.company || "", monthly_price: String(client.monthly_price || "") });
  };

  const openAdd = () => {
    setShowEdit(null); setShowAdd(true); setForm({ name: "", email: "", company: "", monthly_price: "" });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div><h1 className="text-3xl font-bold">Clients</h1><p className="text-muted-foreground">{clients.length} active clients</p></div>
        <Button className="gap-2" onClick={() => setShowAdd(true)}><Plus className="h-4 w-4" /> Add Client</Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>
      ) : clients.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No clients yet</h3>
            <p className="text-sm text-muted-foreground mb-4">Add your first client to start managing their campaigns</p>
        <Button className="gap-2" onClick={openAdd}><Plus className="h-4 w-4" /> Add Client</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {clients.map((client) => (
            <Card key={client.id} className="card-hover">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div><h3 className="font-semibold">{client.name}</h3><p className="text-sm text-muted-foreground">{client.company}</p></div>
                  <Badge variant="outline" className={getStatusColor(client.status)}>{client.status}</Badge>
                </div>
                <div className="space-y-2 text-sm mb-4"><p className="text-muted-foreground">{client.email}</p></div>
                <div className="grid grid-cols-2 gap-3 pt-4 border-t">
                  <div><p className="text-xs text-muted-foreground">MRR</p><p className="font-bold">{formatCurrency(client.monthly_price)}</p></div>
                  <div><p className="text-xs text-muted-foreground">Leads</p><p className="font-bold">{client.total_leads || 0}</p></div>
                  <div><p className="text-xs text-muted-foreground">Campaigns</p><p className="font-bold">{client.total_campaigns || 0}</p></div>
                  <div><p className="text-xs text-muted-foreground">Since</p><p className="font-bold">{formatDate(client.created_at)}</p></div>
                </div>
                <div className="flex gap-2 mt-4 pt-3 border-t">
                  <Button variant="ghost" size="sm" className="gap-1" onClick={() => openEdit(client)}><Edit3 className="h-3 w-3" /> Edit</Button>
                  <Button variant="ghost" size="sm" className="gap-1" onClick={() => handleDelete(client.id)}><Trash2 className="h-3 w-3 text-red-400" /> Delete</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {error && <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">{error}</div>}

      {(showAdd || showEdit) && (
        <div className={MODAL_STYLE} onClick={() => { setShowAdd(false); setShowEdit(null); }}>
          <Card className="w-full max-w-md" onClick={e => e.stopPropagation()}>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{showEdit ? "Edit Client" : "Add Client"}</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => { setShowAdd(false); setShowEdit(null); }}><X className="h-4 w-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input placeholder="Client Name *" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
              <Input placeholder="Email *" type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
              <Input placeholder="Company" value={form.company} onChange={e => setForm({...form, company: e.target.value})} />
              <Input placeholder="Monthly Price ($)" type="number" value={form.monthly_price} onChange={e => setForm({...form, monthly_price: e.target.value})} />
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => { setShowAdd(false); setShowEdit(null); }}>Cancel</Button>
                <Button onClick={showEdit ? handleUpdate : handleAdd} disabled={saving || !form.name || !form.email}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
