"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Zap, ArrowRight, Star, Shield, Globe, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      router.push("/dashboard");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold text-lg bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
            OpenLeads AI
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login">
            <Button variant="ghost">Sign In</Button>
          </Link>
          <Link href="/register">
            <Button>Get Started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 pt-24 pb-16 text-center">
        <div className="mx-auto max-w-4xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/5 px-4 py-1.5 text-sm text-indigo-300 mb-8">
            <Star className="h-4 w-4" />
            AI-Powered Lead Generation Platform
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
            Turn Leads Into
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400"> Revenue</span>
            <br />On Autopilot
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
            Find, qualify, and convert your ideal clients with AI-powered outreach across email, LinkedIn, WhatsApp, and more.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/register">
              <Button size="xl" className="gap-2">
                Start Free Trial <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Button size="xl" variant="outline" onClick={() => {
              document.getElementById("features")?.scrollIntoView({ behavior: "smooth" });
            }}>
              Watch Demo
            </Button>
          </div>
          <p className="text-sm text-gray-500 mt-4">No credit card required • 14-day free trial</p>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-3xl font-bold text-center mb-12">Everything You Need to Scale</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Globe, title: "Multi-Channel Outreach", desc: "Email, LinkedIn, WhatsApp, SMS, Instagram & Twitter/X" },
              { icon: BarChart3, title: "AI Lead Scoring", desc: "GPT-4 powered qualification with 95% accuracy" },
              { icon: Shield, title: "Enterprise Compliance", desc: "GDPR, CAN-SPAM, DMARC, SPF & DKIM ready" },
            ].map((f, i) => (
              <div key={i} className="glass rounded-xl p-6 card-hover">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-500/10 mb-4">
                  <f.icon className="h-6 w-6 text-indigo-400" />
                </div>
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="px-6 py-20 border-t border-white/5">
        <div className="mx-auto max-w-5xl text-center">
          <h2 className="text-3xl font-bold mb-4">Pricing Built for Agencies</h2>
          <p className="text-gray-400 mb-12">Competitive rates. No hidden fees. Cancel anytime.</p>
          <div className="grid md:grid-cols-4 gap-4">
            {[
              { name: "Free", price: "$0", leads: "100", campaigns: "1", features: ["AI lead finder", "Basic scoring", "Email support"] },
              { name: "Starter", price: "$49", leads: "1,000", campaigns: "5", features: ["AI lead finder", "AI scoring", "Email outreach", "LinkedIn", "API access"] },
              { name: "Growth", price: "$99", leads: "5,000", campaigns: "Unlimited", features: ["Everything in Starter", "WhatsApp/SMS", "Multi-channel", "White-label", "Priority support"] },
              { name: "Pro", price: "$199", leads: "Unlimited", campaigns: "Unlimited", features: ["Everything in Growth", "Dedicated account mgr", "Custom integrations", "SLA guarantee", "24/7 phone support"] },
            ].map((p, i) => (
              <div
                key={i}
                className={`rounded-xl border p-5 card-hover ${i === 2 ? "border-indigo-500/50 bg-indigo-500/5 scale-105" : "border-white/10"}`}
              >
                {i === 2 && (
                  <span className="inline-block text-xs font-medium text-indigo-400 bg-indigo-500/10 rounded-full px-3 py-1 mb-3">
                    Most Popular
                  </span>
                )}
                <h3 className="text-lg font-bold mb-1">{p.name}</h3>
                <p className="text-2xl font-bold mb-3">{p.price}<span className="text-sm font-normal text-gray-500">/mo</span></p>
                <p className="text-xs text-gray-500 mb-4">{p.leads} leads • {p.campaigns} campaigns</p>
                <ul className="text-xs text-gray-400 space-y-1.5 mb-5 text-left px-2">
                  {p.features.map((f, j) => (
                    <li key={j} className="flex items-center gap-1.5">
                      <span className="text-indigo-400">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Link href="/register" className="w-full">
                  <Button className="w-full text-sm" variant={i === 2 ? "default" : "outline"} size="sm">
                    {i === 0 ? "Start Free" : "Get Started"}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-6">All plans include 14-day free trial. No credit card required.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 px-6 py-8 text-center text-sm text-gray-500">
        <p>© 2024 OpenLeads AI. Built by Mohammed Idrees — mohammedidrees840@gmail.com</p>
      </footer>
    </div>
  );
}
