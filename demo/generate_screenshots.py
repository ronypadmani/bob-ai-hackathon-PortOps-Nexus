from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def generate_screenshots():
    out_dir = Path(__file__).resolve().parent / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 01-home-dashboard.png
    img1 = Image.new("RGB", (1280, 720), color="#F4F7FB")
    d1 = ImageDraw.Draw(img1)
    
    # Header bar
    d1.rectangle([(0, 0), (1280, 60)], fill="#0F62FE")
    d1.text((30, 20), "Port Operations Copilot | San Pedro Bay Complex | 72-Hour Horizon", fill="white")
    
    # Alert banner
    d1.rectangle([(40, 80), (1240, 130)], fill="#FFF1F1", outline="#DA1E28", width=2)
    d1.text((60, 95), "CRITICAL BOTTLENECK PREDICTED: Terminal T2 at 88/100 Risk (Hours 14-30). Optimizer recommends rerouting 3 vessels.", fill="#DA1E28")
    
    # Metric cards
    for idx, (lbl, val, sub) in enumerate([
        ("Total Vessels", "40 Calls", "72h Window"),
        ("Avg Waiting Time", "28.5 hrs", "-30.7% vs Base"),
        ("Max Waiting Time", "68.2 hrs", "-36.6% vs Base"),
        ("Fleet Dwell Saved", "504.0 hrs", "Productivity Gain"),
        ("Hotspots Mitigated", "1 Active", "3 Rerouted")
    ]):
        x1 = 40 + idx * 245
        d1.rectangle([(x1, 150), (x1 + 230, 230)], fill="white", outline="#D0D7DE", width=1)
        d1.rectangle([(x1, 150), (x1 + 6, 230)], fill="#0F62FE")
        d1.text((x1 + 15, 160), lbl, fill="#525252")
        d1.text((x1 + 15, 180), val, fill="#0F62FE")
        d1.text((x1 + 15, 205), sub, fill="#24A148")

    # Chart 1: Heatmap
    d1.rectangle([(40, 250), (620, 680)], fill="white", outline="#D0D7DE", width=1)
    d1.text((60, 265), "72-Hour Terminal Congestion Risk Heatmap", fill="#161616")
    # Terminals
    terms = ["T1 - Pier 400", "T2 - Pier A (Surge)", "T3 - Long Beach Hub"]
    colors_t = ["#8A3FFC", "#DA1E28", "#24A148"]
    for i, t in enumerate(terms):
        d1.text((60, 310 + i * 110), t, fill="#161616")
        d1.rectangle([(60, 335 + i * 110), (600, 395 + i * 110)], fill=colors_t[i])

    # Chart 2: Baseline vs Optimized
    d1.rectangle([(660, 250), (1240, 680)], fill="white", outline="#D0D7DE", width=1)
    d1.text((680, 265), "Operational Impact: Unoptimized Baseline vs AI & OR-Tools", fill="#161616")
    d1.rectangle([(700, 330), (850, 600)], fill="#FA4D56")
    d1.text((720, 610), "Baseline (41.1h)", fill="#525252")
    d1.rectangle([(900, 420), (1050, 600)], fill="#0F62FE")
    d1.text((920, 610), "Optimized (28.5h)", fill="#0F62FE")

    img1.save(out_dir / "01-home-dashboard.png")

    # 2. 02-query-input.png
    img2 = Image.new("RGB", (1280, 720), color="#F4F7FB")
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([(0, 0), (1280, 60)], fill="#0F62FE")
    d2.text((30, 20), "IBM Bob Port Operations Copilot | Conversational Intelligence", fill="white")
    
    d2.rectangle([(40, 80), (1240, 200)], fill="white", outline="#D0D7DE", width=1)
    d2.text((60, 95), "Quick Operational Queries (Click to Execute):", fill="#161616")
    d2.rectangle([(60, 130), (400, 180)], fill="#E8F0FE", outline="#0F62FE")
    d2.text((75, 145), "🚨 Which terminal is most congested?", fill="#0F62FE")
    d2.rectangle([(420, 130), (760, 180)], fill="#E8F0FE", outline="#0F62FE")
    d2.text((435, 145), "🔀 Which vessels should be rerouted?", fill="#0F62FE")
    d2.rectangle([(780, 130), (1120, 180)], fill="#E8F0FE", outline="#0F62FE")
    d2.text((795, 145), "⚠️ Why is Terminal T2 high risk?", fill="#0F62FE")

    # Chat dialogue
    d2.rectangle([(40, 220), (1240, 600)], fill="white", outline="#D0D7DE", width=1)
    d2.rectangle([(60, 240), (1220, 310)], fill="#F4F4F4")
    d2.text((80, 255), "👤 Shift Supervisor:", fill="#525252")
    d2.text((80, 275), "Which terminal is most likely to become congested and what action should we take?", fill="#161616")

    d2.rectangle([(60, 330), (1220, 560)], fill="#F4F7FB", outline="#0F62FE")
    d2.text((80, 345), "🤖 IBM Bob Port Operations Copilot:", fill="#0F62FE")
    d2.text((80, 370), "Pier A Harbor Central (Terminal T2) is the primary operational bottleneck (Peak Risk: 88/100, Hours 14-30).", fill="#161616")
    d2.text((80, 395), "• Root Cause: 14 incoming container calls (36,500 TEU) converging with 91% yard saturation.", fill="#525252")
    d2.text((80, 420), "• Prescriptive Action: Reroute Vessel V104 ('Ever Golden') to Long Beach Automation Hub (Terminal T3).", fill="#24A148")
    d2.text((80, 445), "• Turnaround Savings: Eliminates 7.2 hours of offshore queue delay and balances yard throughput.", fill="#0F62FE")

    # Chat input bar
    d2.rectangle([(40, 620), (1240, 680)], fill="white", outline="#0F62FE", width=2)
    d2.text((60, 645), "Ask IBM Bob Copilot an operational question (e.g. 'Why was Vessel V104 assigned to Berth B301?')...", fill="#8D8D8D")

    img2.save(out_dir / "02-query-input.png")

    # 3. 03-result-output.png
    img3 = Image.new("RGB", (1280, 720), color="#F4F7FB")
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([(0, 0), (1280, 60)], fill="#0F62FE")
    d3.text((30, 20), "72-Hour Master Operations Schedule & OR-Tools Gantt Chart", fill="white")

    # Gantt section
    d3.rectangle([(40, 80), (1240, 380)], fill="white", outline="#D0D7DE", width=1)
    d3.text((60, 95), "Google OR-Tools CP-SAT Berth Interval Allocation (Non-Overlapping)", fill="#161616")
    berths = ["B101 (T1)", "B102 (T1)", "B201 (T2)", "B202 (T2)", "B301 (T3)", "B302 (T3)"]
    for i, b in enumerate(berths):
        d3.text((60, 130 + i * 40), b, fill="#525252")
        d3.rectangle([(160, 125 + i * 40), (160 + (i*130)%800 + 120, 155 + i * 40)], fill="#0F62FE")
        d3.text((170, 130 + i * 40), f"V{101+i} (Cranes: {3 + i%3})", fill="white")

    # Table section
    d3.rectangle([(40, 400), (1240, 680)], fill="white", outline="#D0D7DE", width=1)
    d3.text((60, 415), "72-Hour Rolling Operational Plan — Active Schedule", fill="#161616")
    headers = ["Vessel ID", "Vessel Name", "Priority", "ETA", "Berth", "Start Hr", "End Hr", "Wait Time", "Cranes", "Status"]
    d3.rectangle([(60, 440), (1220, 470)], fill="#0F62FE")
    for j, h in enumerate(headers):
        d3.text((70 + j * 115, 450), h, fill="white")

    rows = [
        ("V101", "Ever Forward", "CRITICAL", "H 1.3", "B101", "H 2.0", "H 24.5", "0.7h", "5 STS", "STANDARD"),
        ("V102", "Maersk Mc-Kinney", "HIGH", "H 1.9", "B301", "H 2.0", "H 18.2", "0.1h", "4 STS", "REROUTED"),
        ("V103", "CMA CGM Palais", "NORMAL", "H 3.3", "B102", "H 3.5", "H 22.0", "0.2h", "3 STS", "STANDARD"),
        ("V104", "Ever Golden", "CRITICAL", "H 14.0", "B301", "H 14.5", "H 36.0", "0.5h", "5 STS", "REROUTED"),
    ]
    for r_idx, r_data in enumerate(rows):
        y_pos = 480 + r_idx * 45
        bg_col = "#E8F0FE" if r_data[9] == "REROUTED" else "white"
        d3.rectangle([(60, y_pos), (1220, y_pos + 40)], fill=bg_col)
        for c_idx, val in enumerate(r_data):
            t_col = "#0F62FE" if r_data[9] == "REROUTED" else "#161616"
            d3.text((70 + c_idx * 115, y_pos + 12), val, fill=t_col)

    img3.save(out_dir / "03-result-output.png")
    print(f"Generated 3 screenshots in {out_dir}")

if __name__ == "__main__":
    generate_screenshots()
