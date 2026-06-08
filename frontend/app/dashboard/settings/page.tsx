"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { authAPI } from "@/lib/api";
import { User, Mail, Shield, Palette, Loader2, Check } from "lucide-react";

export default function SettingsPage() {
  const [profile, setProfile] = useState({ name: "", email: "", company: "", paypal: "" });
  const [passwords, setPasswords] = useState({ current: "", newPass: "" });
  const [branding, setBranding] = useState({ subdomain: "client1", color: "#6366f1" });
  const [saving, setSaving] = useState(false);
  const [savingPass, setSavingPass] = useState(false);
  const [savingBrand, setSavingBrand] = useState(false);
  const [msg, setMsg] = useState("");
  const [passMsg, setPassMsg] = useState("");
  const [brandMsg, setBrandMsg] = useState("");
  const [loadError, setLoadError] = useState("");

  useEffect(() => { loadProfile(); }, []);

  const loadProfile = async () => {
    try {
      setLoadError("");
      const res = await authAPI.me();
      setProfile({ name: res.data.name, email: res.data.email, company: res.data.company || "", paypal: res.data.paypal_email || "" });
      if (res.data.subdomain) setBranding(prev => ({ ...prev, subdomain: res.data.subdomain }));
      if (res.data.brand_color) setBranding(prev => ({ ...prev, color: res.data.brand_color }));
    } catch (err) { setLoadError("Failed to load profile"); }
  };

  const handleSaveProfile = async () => {
    setSaving(true); setMsg("");
    try { await authAPI.updateMe({ name: profile.name, company: profile.company }); setMsg("Profile saved!"); }
    catch (err) { setMsg("Failed to save"); }
    finally { setSaving(false); }
  };

  const handleSavePassword = async () => {
    if (!passwords.current || !passwords.newPass) { setPassMsg("Fill both fields"); return; }
    setSavingPass(true); setPassMsg("");
    try {
      await authAPI.changePassword({ current_password: passwords.current, new_password: passwords.newPass });
      setPassMsg("Password updated!"); setPasswords({ current: "", newPass: "" });
    } catch (err: any) { setPassMsg(err.response?.data?.detail || "Failed to update password"); }
    finally { setSavingPass(false); }
  };

  const handleSaveBranding = async () => {
    setSavingBrand(true); setBrandMsg("");
    try {
      await authAPI.updateMe({ subdomain: branding.subdomain, brand_color: branding.color });
      setBrandMsg("Branding saved!");
    } catch (err) { setBrandMsg("Failed to save"); }
    finally { setSavingBrand(false); }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div><h1 className="text-3xl font-bold">Settings</h1><p className="text-muted-foreground">Manage your account and preferences</p></div>

      {loadError && <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">{loadError}</div>}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg"><User className="h-5 w-5 text-primary" /> Profile</CardTitle>
            <CardDescription>Your personal information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div><label className="text-sm font-medium mb-1 block">Full Name</label><Input value={profile.name} onChange={e => setProfile({...profile, name: e.target.value})} /></div>
            <div><label className="text-sm font-medium mb-1 block">Email</label><Input value={profile.email} disabled className="opacity-60" /></div>
            <div><label className="text-sm font-medium mb-1 block">Company</label><Input value={profile.company} onChange={e => setProfile({...profile, company: e.target.value})} /></div>
            <div><label className="text-sm font-medium mb-1 block">PayPal Email</label><Input value={profile.paypal} disabled className="opacity-60" /></div>
            {msg && <p className="text-sm text-green-500 flex items-center gap-1"><Check className="h-3 w-3" /> {msg}</p>}
            <Button onClick={handleSaveProfile} disabled={saving}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Changes"}</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg"><Shield className="h-5 w-5 text-primary" /> Security</CardTitle>
            <CardDescription>Password and authentication</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div><label className="text-sm font-medium mb-1 block">Current Password</label><Input type="password" placeholder="••••••••" value={passwords.current} onChange={e => setPasswords({...passwords, current: e.target.value})} /></div>
            <div><label className="text-sm font-medium mb-1 block">New Password</label><Input type="password" placeholder="••••••••" value={passwords.newPass} onChange={e => setPasswords({...passwords, newPass: e.target.value})} /></div>
            {passMsg && <p className={`text-sm flex items-center gap-1 ${passMsg.includes("updated") ? "text-green-500" : "text-red-500"}`}><Check className="h-3 w-3" /> {passMsg}</p>}
            <Button onClick={handleSavePassword} disabled={savingPass}>{savingPass ? <Loader2 className="h-4 w-4 animate-spin" /> : "Update Password"}</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg"><Palette className="h-5 w-5 text-primary" /> White-Label</CardTitle>
            <CardDescription>Client portal branding</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Subdomain</label>
              <div className="flex items-center gap-2">
                <Input value={branding.subdomain} className="flex-1" onChange={e => setBranding({...branding, subdomain: e.target.value})} />
                <span className="text-muted-foreground">.openleads.ai</span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Brand Color</label>
              <div className="flex gap-2">
                {["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"].map((c) => (
                  <button key={c} className={`h-8 w-8 rounded-full border-2 transition-all ${branding.color === c ? "border-white scale-110" : "border-transparent"}`} style={{ backgroundColor: c }} onClick={() => setBranding({...branding, color: c})} />
                ))}
              </div>
            </div>
            {brandMsg && <p className="text-sm text-green-500 flex items-center gap-1"><Check className="h-3 w-3" /> {brandMsg}</p>}
            <Button onClick={handleSaveBranding} disabled={savingBrand}>{savingBrand ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Branding"}</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg"><Mail className="h-5 w-5 text-primary" /> Pricing Tiers</CardTitle>
            <CardDescription>Your agency pricing structure</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { name: "Starter", price: "$299/mo", leads: "500 leads/mo", color: "text-blue-500" },
              { name: "Growth", price: "$599/mo", leads: "2,000 leads/mo", color: "text-green-500" },
              { name: "Pro", price: "$1,199/mo", leads: "10,000 leads/mo", color: "text-purple-500" },
              { name: "Enterprise", price: "$2,999/mo", leads: "Unlimited", color: "text-orange-500" },
            ].map((tier, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
                <div><p className="font-medium">{tier.name}</p><p className="text-sm text-muted-foreground">{tier.leads}</p></div>
                <p className={`text-lg font-bold ${tier.color}`}>{tier.price}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
