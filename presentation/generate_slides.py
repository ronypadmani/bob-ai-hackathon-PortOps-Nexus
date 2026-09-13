import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_presentation_pdf(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(letter),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom slide styles
    title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontSize=26,
        leading=30,
        textColor=colors.HexColor('#0F62FE'),
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'SlideSubtitle',
        parent=styles['Normal'],
        fontSize=15,
        leading=20,
        textColor=colors.HexColor('#393939'),
        spaceAfter=25
    )
    
    body_style = ParagraphStyle(
        'SlideBody',
        parent=styles['Normal'],
        fontSize=12,
        leading=18,
        textColor=colors.HexColor('#161616'),
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        'SlideBullet',
        parent=styles['Normal'],
        fontSize=12,
        leading=18,
        textColor=colors.HexColor('#262626'),
        leftIndent=20,
        spaceAfter=8
    )

    story = []

    # Slide 1: Title Slide
    story.append(Spacer(1, 40))
    story.append(Paragraph("Port Operations Copilot", title_style))
    story.append(Paragraph("AI-Driven Congestion Hotspot Prediction, Prescriptive Google OR-Tools Optimization, & 72-Hour Rolling Operational Planning", subtitle_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>IBM Bob AI Hackathon 2026</b> | Team PortOps Nexus | Track: AI", body_style))
    story.append(Paragraph("Dhairya Isotiya (Lead), Darshil Kothiya, Rony Padmani, Harsh Dobariya", body_style))
    story.append(PageBreak())

    # Slide 2: Problem Statement
    story.append(Paragraph("1. The Problem: The $10B+ Global Port Congestion Crisis", title_style))
    story.append(Paragraph("The 2021 LA / Long Beach port crisis left 100+ container vessels idling offshore for weeks.", subtitle_style))
    story.append(Paragraph("• <b>Manual Spreadsheet Scheduling</b>: Berths, cranes, and yard slots are allocated via static spreadsheets, blind to holistic constraints.", bullet_style))
    story.append(Paragraph("• <b>Reactive Bottleneck Discovery</b>: Congestion is detected only after ships have already formed long offshore queues.", bullet_style))
    story.append(Paragraph("• <b>Delayed Rerouting Decisions</b>: Shippers and terminal operators lack foresight to divert incoming calls to under-utilized partner berths before bottlenecks escalate.", bullet_style))
    story.append(Paragraph("• <b>Multi-Billion Dollar Impact</b>: Demurrage fees, intermodal rail disruption, and massive supply chain inflation.", bullet_style))
    story.append(PageBreak())

    # Slide 3: Solution Architecture & Innovation
    story.append(Paragraph("2. The Solution: Intelligent Port Operations Copilot", title_style))
    story.append(Paragraph("A closed-loop AI & Mathematical Optimization decision support system.", subtitle_style))
    story.append(Paragraph("• <b>Predictive Risk Engine</b>: Sliding-window ML (Random Forest) + domain heuristics forecast congestion hotspots up to 72h ahead.", bullet_style))
    story.append(Paragraph("• <b>Google OR-Tools CP-SAT</b>: Exact mathematical constraint programming schedules non-overlapping berth windows and eliminates waiting times.", bullet_style))
    story.append(Paragraph("• <b>Dynamic Crane Allocation</b>: Allocates 2-5 STS cranes per vessel based on TEU workload and vessel priority class.", bullet_style))
    story.append(Paragraph("• <b>Proactive Alternate Routing</b>: Recommends feasible diversions with verified draft/LOA clearance before vessels arrive.", bullet_style))
    story.append(PageBreak())

    # Slide 4: IBM Bob & watsonx Integration
    story.append(Paragraph("3. IBM Bob & watsonx AI Integration", title_style))
    story.append(Paragraph("IBM Bob is deeply load-bearing across development and runtime operations.", subtitle_style))
    story.append(Paragraph("• <b>Engineering Acceleration</b>: IBM Bob steered architecture design, OR-Tools CP-SAT modeling, and automated test synthesis.", bullet_style))
    story.append(Paragraph("• <b>Conversational Copilot</b>: Grounded in live port state (vessel ETAs, berth schedules, crane metrics, risk scores).", bullet_style))
    story.append(Paragraph("• <b>watsonx Granite 3.0 Integration</b>: Orchestrates domain-specific prompts with live telemetry injection.", bullet_style))
    story.append(Paragraph("• <b>6-Point Explainability Audit</b>: Every assignment answers What happened, Why problem, System prediction, Recommended action, Why selected, and Constraints verified.", bullet_style))
    story.append(PageBreak())

    # Slide 5: Measurable Impact & Live Results
    story.append(Paragraph("4. Measurable Operational Impact", title_style))
    story.append(Paragraph("Comparing Baseline (Naive FIFO) vs AI & OR-Tools Optimized Schedule:", subtitle_style))
    
    kpi_table_data = [
        ["Operational Metric", "Unoptimized Baseline", "AI & OR-Tools Optimized", "Impact Delta"],
        ["Average Vessel Waiting Time", "41.1 Hours", "28.5 Hours", "30.7% Reduction"],
        ["Maximum Vessel Queue Delay", "107.5 Hours", "68.2 Hours", "36.6% Reduction"],
        ["Congested Delayed Vessels (>3h)", "32 Vessels", "18 Vessels", "14 Vessels Saved"],
        ["Fleet Port Dwell Time Saved", "—", "—", "504+ Vessel-Hours Saved"],
        ["Proactive Reroutings Executed", "0 (Reactive)", "3 Diversions", "Hotspot Eradicated"]
    ]
    t = Table(kpi_table_data, colWidths=[200, 140, 160, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F62FE')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F4F7FB')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D0D7DE')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    story.append(t)
    story.append(PageBreak())

    # Slide 6: What's Next & Vision
    story.append(Paragraph("5. Future Vision & Enterprise Roadmap", title_style))
    story.append(Paragraph("From Hackathon Prototype to Global Maritime TOS Standard:", subtitle_style))
    story.append(Paragraph("• <b>Real-Time AIS Vessel Telemetry</b>: Live satellite feed ingestion for sub-hourly ETA updates.", bullet_style))
    story.append(Paragraph("• <b>Intermodal Rail & Drayage Truck Sync</b>: Extending optimization into container yards and railheads.", bullet_style))
    story.append(Paragraph("• <b>Port Multi-Terminal Federation</b>: Unified optimization across entire port authorities (e.g. LA, Long Beach, Rotterdam, Singapore).", bullet_style))
    story.append(Paragraph("• <b>watsonx Governance</b>: Full model lifecycle monitoring, compliance tracking, and audit logging.", bullet_style))

    doc.build(story)
    print(f"Generated presentation PDF at {output_path}")

if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent / "slides.pdf"
    create_presentation_pdf(out_file)
