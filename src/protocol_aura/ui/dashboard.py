import streamlit as st
import plotly.graph_objects as go
import asyncio
import json
import hashlib
from datetime import datetime

from protocol_aura.agents import BoutiqueAgent, ShopperAgent
from protocol_aura.protocol import Mandate
from protocol_aura.core.negotiation import negotiation_engine
from protocol_aura.data import get_all_boutiques

st.set_page_config(page_title="Protocol: Aura", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.main{background:linear-gradient(135deg,#0a0a0f 0%,#1a1a2e 50%,#16213e 100%)}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;background:linear-gradient(90deg,#667eea 0%,#764ba2 50%,#f093fb 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.transcript{background:rgba(255,255,255,0.03);border-radius:12px;padding:16px;margin:8px 0;border-left:4px solid #667eea}
.transcript.store{border-left-color:#f093fb}
.status-accepted{color:#00f5a0;font-weight:600}
.status-rejected{color:#f56565;font-weight:600}
.match-score{font-size:28px;font-weight:700}
.match-high{color:#00f5a0}
.match-medium{color:#f5a623}
.match-low{color:#f56565}
.option-card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:14px;margin:6px 0}
.option-valid{border-color:#00f5a0;box-shadow:0 0 8px rgba(0,245,160,0.2)}
.option-invalid{border-color:#f56565;opacity:0.8}
.product-card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:12px;text-align:center;margin:4px}
.product-price{font-size:20px;font-weight:700;color:#00f5a0}
.transform{font-size:12px;color:rgba(255,255,255,0.85);padding:6px 10px;background:rgba(0,0,0,0.25);border-radius:6px;margin:4px 0;border-left:3px solid #f093fb}
.mandate-box{background:rgba(102,126,234,0.15);border:1px solid rgba(102,126,234,0.3);border-radius:8px;padding:12px;margin:8px 0;font-size:13px}
.best-header{background:rgba(0,245,160,0.1);border:1px solid rgba(0,245,160,0.3);border-radius:10px;padding:14px;margin:8px 0}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def create_radar(axes: dict) -> go.Figure:
    cats = list(axes.keys())
    vals = [max(0, min(1, v)) for v in axes.values()]
    vals.append(vals[0])
    cats.append(cats[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals, theta=cats, fill='toself', line=dict(color='#667eea', width=2), fillcolor='rgba(102,126,234,0.3)'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=9, color='rgba(255,255,255,0.5)'), gridcolor='rgba(255,255,255,0.1)'), angularaxis=dict(tickfont=dict(size=10, color='rgba(255,255,255,0.7)'), gridcolor='rgba(255,255,255,0.1)'), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(l=50, r=50, t=25, b=25), height=260)
    return fig


def status_display(status) -> str:
    s = str(status.value) if hasattr(status, 'value') else str(status)
    m = {"accepted": ("✅", "DONE (ACCEPTED)", "status-accepted"), "rejected": ("❌", "DONE (REJECTED)", "status-rejected"), "responded": ("📥", "RESPONDED", ""), "pending": ("⏳", "PENDING", "")}
    icon, text, css = m.get(s.lower(), ("❓", s.upper(), ""))
    return f'<span class="{css}">{icon} {text}</span>'


def render_transcript(transcript: list, store_name: str):
    for e in transcript:
        t = e.get('turn', '?')
        speaker = e['speaker']
        typ = e['type']
        content = e['content']
        details = e.get('details', {})
        
        if speaker == 'Shopper':
            st.markdown(f'<div class="transcript"><strong>Turn {t} · 🛒 Shopper</strong> [{typ}]<br/>{content}</div>', unsafe_allow_html=True)
            if typ == 'REJECT' and details.get('would_accept_if'):
                st.info(f"💡 Would accept if: {details['would_accept_if']}")
        else:
            st.markdown(f'<div class="transcript store"><strong>Turn {t} · 🏪 {speaker}</strong> [{typ}] · {details.get("latency_ms", 0)}ms</div>', unsafe_allow_html=True)
            
            if details.get('option_a'):
                a = details['option_a']
                b = details.get('option_b')
                
                a_match_pct = a.get('match', '0%').replace('%', '')
                a_dist_pct = a.get('distance', '0%').replace('%', '')
                
                c1, c2 = st.columns(2)
                with c1:
                    valid_css = "option-valid" if a.get('budget_ok') else "option-invalid"
                    ok = "✓ valid" if a.get('budget_ok') else "✗ invalid"
                    st.markdown(f'''<div class="option-card {valid_css}">
                        <strong>Option A (Budget-fit)</strong> {ok}<br/>
                        Match: <strong>{a["match"]}</strong><br/>
                        Distance: {a["distance"]}<br/>
                        Price: {a["price"]}<br/>
                        <small>{", ".join(a["products"][:2])}</small>
                    </div>''', unsafe_allow_html=True)
                
                if b:
                    with c2:
                        valid_css = "option-valid" if b.get('budget_ok') else "option-invalid"
                        if b.get('budget_ok'):
                            ok_line = "✓ valid"
                        else:
                            try:
                                b_price = float(b["price"].replace("$", "").replace(",", ""))
                                budget_val = float(a["price"].replace("$", "").replace(",", "")) * 2
                                over = b_price - budget_val if budget_val > 0 else 0
                            except:
                                over = 0
                            ok_line = f"✗ invalid — exceeds budget"
                        st.markdown(f'''<div class="option-card {valid_css}">
                            <strong>Option B (Vibe-fit)</strong> {ok_line}<br/>
                            Match: <strong>{b["match"]}</strong><br/>
                            Distance: {b["distance"]}<br/>
                            Price: {b["price"]}<br/>
                            <small>{", ".join(b["products"][:2])}</small>
                        </div>''', unsafe_allow_html=True)
            
            transforms = details.get('transformations', [])
            if transforms:
                with st.expander("📐 Vibe Transformations", expanded=True):
                    for tr in transforms:
                        st.markdown(f'<div class="transform">{tr}</div>', unsafe_allow_html=True)
                    st.caption("💡 Bundle A preserves core vibe while adjusting select axes to stay within budget.")


def get_accepted_offer_info(session):
    if not session.final_result or not hasattr(session.final_result, 'accepted_bundle'):
        return None
    
    for r in session.rounds:
        if hasattr(r, 'store_message') and r.store_message:
            msg = r.store_message
            if hasattr(msg, 'option_a'):
                bundle = msg.option_a if session.final_result.accepted_bundle == 'A' else msg.option_b
                if bundle:
                    return {
                        'bundle': session.final_result.accepted_bundle,
                        'match': bundle.match_score,
                        'distance': bundle.vibe_distance,
                        'price': bundle.total_price,
                    }
    return None


def get_both_offers_info(session):
    for r in session.rounds:
        if hasattr(r, 'store_message') and r.store_message:
            msg = r.store_message
            if hasattr(msg, 'option_a'):
                opt_a = msg.option_a
                opt_b = msg.option_b
                return {
                    "option_a": {
                        "type": opt_a.bundle_type,
                        "match": opt_a.match_score,
                        "distance": opt_a.vibe_distance,
                        "price": opt_a.total_price,
                        "valid": all(c.satisfied for c in opt_a.constraint_checks),
                        "products": [p.name for p in opt_a.products],
                    },
                    "option_b": {
                        "type": opt_b.bundle_type if opt_b else None,
                        "match": opt_b.match_score if opt_b else None,
                        "distance": opt_b.vibe_distance if opt_b else None,
                        "price": opt_b.total_price if opt_b else None,
                        "valid": all(c.satisfied for c in opt_b.constraint_checks) if opt_b else False,
                        "products": [p.name for p in opt_b.products] if opt_b else [],
                    } if opt_b else None,
                }
    return None


def vibe_receipt(session, boutique, prompt, budget) -> dict:
    transcript = negotiation_engine.get_transcript(session)
    accepted_info = get_accepted_offer_info(session)
    both_offers = get_both_offers_info(session)
    
    receipt = {
        "protocol": "AURA v0.1",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "session": {
            "id": session.session_id,
            "store_id": session.store_id,
            "store_name": session.store_name,
            "turns": f"{session.turns_used}/{session.max_turns}",
            "latency_ms": session.latency_ms,
            "status": str(session.status.value),
        },
        "query": {"emotional_prompt": prompt},
        "mandate": {
            "budget_cap": budget,
            "budget_type": "hard_constraint",
            "auto_accept_rule": "highest match among valid offers",
        },
        "offers": both_offers,
        "chosen_offer": accepted_info,
        "selected_items": [],
        "axis_deltas": [],
        "transcript_hash": hashlib.sha256(json.dumps(transcript, sort_keys=True).encode()).hexdigest(),
    }
    
    if session.final_result and hasattr(session.final_result, 'accepted_products'):
        receipt["selected_items"] = [
            {"name": p.name, "price": p.price, "category": p.category}
            for p in session.final_result.accepted_products
        ]
        receipt["axis_deltas"] = [
            {"axis": t.axis, "from": t.from_value, "to": t.to_value, "delta": t.delta, "item_change": t.item_change}
            for t in session.final_result.transformations_accepted
        ]
    
    return receipt


async def run_negotiation(prompt: str, budget: float, context: str):
    mandate = Mandate(user_id="shopper", budget_cap=budget, auto_purchase_enabled=False)
    shopper = ShopperAgent(user_id="shopper", user_name="Shopper Agent", mandate=mandate, style_goal=prompt)
    
    sessions = []
    for b in get_all_boutiques():
        boutique = BoutiqueAgent(store_id=b.store_id, store_name=b.store_name, manifold=b, flexibility=0.55)
        s = await negotiation_engine.start_negotiation(shopper=shopper, boutique=boutique, emotional_prompt=prompt, context=context)
        sessions.append((b, s))
    return sessions


def main():
    st.markdown("# ✨ Protocol: Aura")
    st.caption("Agent-to-Agent Negotiation · Aesthetic Commerce Protocol")
    st.markdown("---")
    
    with st.sidebar:
        st.markdown("### ⚙️ Shopper Mandate")
        budget = st.slider("Budget Cap ($)", 50, 1000, 400, 50)
        
        st.markdown(f'''<div class="mandate-box">
            <strong>🤖 Autonomous Rules</strong><br/>
            • Budget: <strong>${budget}</strong> (hard constraint)<br/>
            • Max items: 3<br/>
            • Auto-accept best valid offer
        </div>''', unsafe_allow_html=True)
        
        st.caption("Match = 1 − distance (L2 on 8-axis vibe)")
        
        st.markdown("---")
        st.markdown("### 🏪 Boutiques")
        for b in get_all_boutiques():
            with st.expander(b.store_name):
                st.caption(b.vibe_center.description[:80])
    
    c1, c2 = st.columns([3, 2])
    with c1:
        prompt = st.text_input("Your aesthetic goal", placeholder="CEO who codes at night and DJs on weekends")
        context = st.text_input("Context (optional)", placeholder="Tech conference in Berlin")
        if st.button("🚀 Negotiate", type="primary", use_container_width=True):
            if prompt:
                with st.spinner("Agents negotiating..."):
                    st.session_state['nego'] = asyncio.run(run_negotiation(prompt, budget, context))
                    st.session_state['p'] = prompt
                    st.session_state['b'] = budget
    
    with c2:
        if 'nego' in st.session_state and st.session_state['nego']:
            accepted_sessions = []
            for b, s in st.session_state['nego']:
                if str(s.status.value) == 'accepted':
                    info = get_accepted_offer_info(s)
                    if info:
                        accepted_sessions.append((b, s, info))
            
            if accepted_sessions:
                best = max(accepted_sessions, key=lambda x: x[2]['match'])
                boutique, session, info = best
                match_cls = "match-high" if info['match'] >= 0.85 else ("match-medium" if info['match'] >= 0.70 else "match-low")
                
                st.markdown(f'''<div class="best-header">
                    <strong>Best Valid Offer: {boutique.store_name} (Option {info['bundle']})</strong><br/>
                    <span class="match-score {match_cls}">{info['match']:.0%}</span> match · {info['distance']:.0%} distance · ${info['price']:.0f} ✓<br/>
                    <small>Responded in {getattr(session, 'latency_ms', 0)}ms</small>
                </div>''', unsafe_allow_html=True)
            else:
                st.warning("No valid offers within budget constraint")
    
    if 'nego' in st.session_state:
        st.markdown("---")
        st.markdown("## 🤝 Negotiation Results")
        tabs = st.tabs([s[0].store_name for s in st.session_state['nego']])
        
        for i, (boutique, session) in enumerate(st.session_state['nego']):
            with tabs[i]:
                l, r = st.columns([1, 2])
                
                accepted_info = get_accepted_offer_info(session)
                
                with l:
                    st.plotly_chart(create_radar(boutique.vibe_center.axes), use_container_width=True)
                    
                    if accepted_info:
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Match", f"{accepted_info['match']:.0%}")
                        m2.metric("Turns", f"{getattr(session, 'turns_used', 1)}/{session.max_turns}")
                        m3.metric("Latency", f"{getattr(session, 'latency_ms', 0)}ms")
                        st.caption(f"Distance: {accepted_info['distance']:.0%} · Bundle: {accepted_info['bundle']}")
                    else:
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Match", "—")
                        m2.metric("Turns", f"{getattr(session, 'turns_used', 1)}/{session.max_turns}")
                        m3.metric("Latency", f"{getattr(session, 'latency_ms', 0)}ms")
                    
                    st.markdown(f"**Status:** {status_display(session.status)}", unsafe_allow_html=True)
                
                with r:
                    st.markdown("### 💬 Transcript")
                    render_transcript(negotiation_engine.get_transcript(session), session.store_name)
                
                if session.final_result and hasattr(session.final_result, 'accepted_products'):
                    st.markdown("### 🛍️ Selected Items")
                    cols = st.columns(min(3, len(session.final_result.accepted_products)))
                    for j, p in enumerate(session.final_result.accepted_products):
                        with cols[j % 3]:
                            st.markdown(f'<div class="product-card"><strong>{p.name}</strong><br/><small>{p.category}</small><br/><div class="product-price">${p.price:.0f}</div></div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    receipt = vibe_receipt(session, boutique, st.session_state['p'], st.session_state['b'])
                    st.download_button("📜 Export Vibe Receipt", json.dumps(receipt, indent=2), f"vibe_receipt_{session.store_id}.json", "application/json")
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;color:rgba(255,255,255,0.5);font-size:12px">
        <strong>Protocol: Aura v0.1</strong><br/>
        <em>"AURA turns aesthetics into a negotiable contract between agents."</em>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
