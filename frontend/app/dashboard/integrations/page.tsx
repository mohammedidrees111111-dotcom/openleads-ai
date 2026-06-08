"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { integrationsAPI } from "@/lib/api";
import { Plug, Link2, Unlink, Check, X, Loader2 } from "lucide-react";

const MODAL_STYLE = "fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm";

const INTEGRATIONS_LIST = [
  { name: "HubSpot", desc: "CRM sync", color: "from-orange-500/10 to-orange-600/5 border-orange-500/20", fields: [{ key: "api_key", label: "API Key", type: "password" }, { key: "portal_id", label: "Portal ID" }] },
  { name: "Salesforce", desc: "CRM sync", color: "from-blue-500/10 to-blue-600/5 border-blue-500/20", fields: [{ key: "client_id", label: "Client ID" }, { key: "client_secret", label: "Client Secret", type: "password" }] },
  { name: "Pipedrive", desc: "CRM sync", color: "from-green-500/10 to-green-600/5 border-green-500/20", fields: [{ key: "api_token", label: "API Token", type: "password" }] },
  { name: "Zoho CRM", desc: "CRM sync", color: "from-red-500/10 to-red-600/5 border-red-500/20", fields: [{ key: "client_id", label: "Client ID" }, { key: "client_secret", label: "Client Secret", type: "password" }] },
  { name: "Google Sheets", desc: "Data export", color: "from-emerald-500/10 to-emerald-600/5 border-emerald-500/20", fields: [{ key: "api_key", label: "API Key", type: "password" }] },
  { name: "Clearbit", desc: "Data enrichment", color: "from-purple-500/10 to-purple-600/5 border-purple-500/20", fields: [{ key: "api_key", label: "API Key", type: "password" }] },
  { name: "Hunter.io", desc: "Email finding", color: "from-pink-500/10 to-pink-600/5 border-pink-500/20", fields: [{ key: "api_key", label: "API Key", type: "password" }] },
  { name: "Apollo.io", desc: "Contact enrichment", color: "from-indigo-500/10 to-indigo-600/5 border-indigo-500/20", fields: [{ key: "api_key", label: "API Key", type: "password" }] },
  { name: "Stripe", desc: "Billing", color: "from-violet-500/10 to-violet-600/5 border-violet-500/20", fields: [{ key: "secret_key", label: "Secret Key", type: "password" }] },
  { name: "PayPal", desc: "Billing", color: "from-sky-500/10 to-sky-600/5 border-sky-500/20", fields: [{ key: "client_id", label: "Client ID" }, { key: "client_secret", label: "Client Secret", type: "password" }] },
  { name: "Twilio", desc: "SMS", color: "from-rose-500/10 to-rose-600/5 border-rose-500/20", fields: [{ key: "account_sid", label: "Account SID" }, { key: "auth_token", label: "Auth Token", type: "password" }] },
  { name: "WhatsApp", desc: "Messaging", color: "from-teal-500/10 to-teal-600/5 border-teal-500/20", fields: [{ key: "api_key", label: "API Key", type: "password" }, { key: "phone_id", label: "Phone ID" }] },
  { name: "LinkedIn", desc: "Social outreach", color: "from-blue-500/10 to-blue-600/5 border-blue-500/20", fields: [{ key: "email", label: "Email" }, { key: "password", label: "Password", type: "password" }] },
  { name: "n8n", desc: "Workflow automation", color: "from-gray-500/10 to-gray-600/5 border-gray-500/20", fields: [{ key: "webhook_url", label: "Webhook URL" }] },
  { name: "Zapier", desc: "Workflow automation", color: "from-yellow-500/10 to-yellow-600/5 border-yellow-500/20", fields: [{ key: "webhook_url", label: "Webhook URL" }] },
];

export default function IntegrationsPage() {
  const [connected, setConnected] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [showConnect, setShowConnect] = useState<string | null>(null);
  const [creds, setCreds] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  useEffect(() => { loadConnected(); }, []);

  const loadConnected = async () => {
    setError("");
    try {
      const res = await integrationsAPI.list();
      const map: Record<string, any> = {};
      (res.data || []).forEach((i: any) => { map[i.provider] = i; });
      setConnected(map);
    } catch (err) { setError("Failed to load integrations"); }
    finally { setLoading(false); }
  };

  const handleConnect = async (provider: string) => {
    setConnecting(provider); setError("");
    try {
      await integrationsAPI.connect(provider, creds);
      setShowConnect(null); setCreds({}); loadConnected();
    } catch (err) { setError("Failed to connect integration"); }
    finally { setConnecting(null); }
  };

  const handleDisconnect = async (provider: string) => {
    const integration = connected[provider];
    if (!integration?.id) return;
    try {
      await integrationsAPI.disconnect(integration.id);
      loadConnected();
    } catch (err) { setError("Failed to disconnect"); }
  };

  const integration = INTEGRATIONS_LIST.find(i => i.name.toLowerCase().replace(/\s+/g, "-") === showConnect);

  return (
    <div className="space-y-6 animate-fade-in">
      <div><h1 className="text-3xl font-bold">Integrations</h1><p className="text-muted-foreground">Connect your favorite tools and services</p></div>

      {error && <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">{error}</div>}

      {loading ? <div className="flex items-center justify-center h-64"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div> : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {INTEGRATIONS_LIST.map((intg, i) => {
            const prov = intg.name.toLowerCase().replace(/\s+/g, "-");
            const isConnected = !!connected[prov];
            return (
              <Card key={i} className={`bg-gradient-to-br ${intg.color} card-hover`}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background"><Plug className="h-5 w-5" /></div>
                    <div><p className="font-medium text-sm">{intg.name}</p><p className="text-xs text-muted-foreground">{intg.desc}</p></div>
                  </div>
                  {isConnected ? (
                    <div className="flex gap-2">
                      <Badge variant="success" className="gap-1"><Check className="h-3 w-3" /> Connected</Badge>
                      <Button variant="outline" size="sm" className="gap-1" onClick={() => handleDisconnect(prov)}><Unlink className="h-3 w-3" /> Disconnect</Button>
                    </div>
                  ) : (
                    <Button variant="outline" size="sm" className="w-full gap-1" onClick={() => { setShowConnect(prov); setCreds({}); }}>
                      <Link2 className="h-3 w-3" /> Connect
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {showConnect && integration && (
        <div className={MODAL_STYLE} onClick={() => setShowConnect(null)}>
          <Card className="w-full max-w-md" onClick={e => e.stopPropagation()}>
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center justify-between"><h3 className="font-semibold text-lg">Connect {integration.name}</h3><Button variant="ghost" size="icon" onClick={() => setShowConnect(null)}><X className="h-4 w-4" /></Button></div>
              <p className="text-sm text-muted-foreground">Enter your {integration.name} credentials</p>
              {integration.fields.map(f => (
                <div key={f.key}>
                  <label className="text-sm font-medium mb-1 block">{f.label}</label>
                  <Input type={f.type || "text"} value={creds[f.key] || ""} onChange={e => setCreds({...creds, [f.key]: e.target.value})} />
                </div>
              ))}
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setShowConnect(null)}>Cancel</Button>
                <Button onClick={() => handleConnect(showConnect)} disabled={connecting === showConnect}>
                  {connecting === showConnect ? <Loader2 className="h-4 w-4 animate-spin" /> : "Connect"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
