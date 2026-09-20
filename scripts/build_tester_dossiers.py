"""Generator/validator script for the 15 tester accounts."""
import json

def get_15_dossiers():
    return [
        # =====================================================================
        # 5 PENDING TESTER ACCOUNTS (Standard In-Progress Turnover & Audits)
        # =====================================================================
        {
            "dossier_id": "DOS-2026-001",
            "employee_name": "Juan Dela Cruz",
            "employee_id": "EMP-94812",
            "department": "Information Technology",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Senior Specialist",
            "branch": "Taguig HQ - 24th Floor",
            "date_hired": "2022-03-15",
            "eoc_date": "2026-08-31",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_1_ASSET",
            "stage_name": "Stage 1: Asset Hand-Off & Turnover",
            "stage_step": 1,
            "current_turn_node": "IT",
            "current_turn_name": "Alex Tan (IT Clearance Lead)",
            "current_turn_role": "IT_APPROVER",
            "current_turn_action": "Verify Lenovo ThinkPad T14s serial number (20WM-0045PH) and complete corporate device wipe.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-18T08:30:00Z",
            "sample_file": "clearance_missing_it.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Alex Tan (IT Clearance Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "PENDING", "summary": "Physical laptop inspection in progress"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Locker #24 & Parking Tag Cleared"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "CLEARED", "summary": "No cash advances outstanding"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting IT hardware clearance"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Juan Dela Cruz (Employee)",
                    "date": "2026-08-31 09:15 AM",
                    "status": "COMPLETED",
                    "details": "Resignation clearance lodged via Lark Form for Taguig Corporate HQ.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "Company Laptop Hand-Off",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-02 11:30 AM",
                    "status": "IN_PROGRESS",
                    "details": "Lenovo ThinkPad T14s received at Taguig HQ reception. Serial 20WM-0045PH verified. Data sanitization in progress.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Physical Locker Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-03 02:00 PM",
                    "status": "COMPLETED",
                    "details": "Office Locker #24 padlock surrendered. 24th Floor turnstile RFID transponder deactivated.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-04 10:15 AM",
                    "status": "COMPLETED",
                    "details": "Pro-rated salary (₱32,000.00) & 13th month (₱16,500.00) audited. Net final pay: ₱48,500.00.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "Quit Claim & Waiver Sign-Off",
                    "actor": "Juan Dela Cruz (Employee)",
                    "date": "Pending Turn",
                    "status": "PENDING",
                    "details": "Awaiting IT hardware completion before final waiver execution.",
                    "icon": "fa-signature"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to BDO account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-101",
                    "author": "Alex Tan",
                    "role": "IT_APPROVER",
                    "text": "Lenovo ThinkPad T14s received at Taguig HQ reception. S/N: 20WM-0045PH. Device diagnostics healthy.",
                    "timestamp": "2026-09-02T11:45:00Z"
                },
                {
                    "id": "cmt-102",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "Net final payout confirmed at ₱48,500.00. Ready for release once IT signs off.",
                    "timestamp": "2026-09-04T10:30:00Z"
                },
                {
                    "id": "cmt-103",
                    "author": "Juan Dela Cruz",
                    "role": "REQUESTER",
                    "text": "Acknowledged and verified bank account proof. Standing by for final release.",
                    "timestamp": "2026-09-04T14:10:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-003",
            "employee_name": "Angela Soriano",
            "employee_id": "EMP-83104",
            "department": "Marketing & Brand",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Specialist / Professional",
            "branch": "Makati Central Hub",
            "date_hired": "2023-04-10",
            "eoc_date": "2026-09-22",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_1_ASSET",
            "stage_name": "Stage 1: Asset Hand-Off & Turnover",
            "stage_step": 1,
            "current_turn_node": "ADMIN",
            "current_turn_name": "Elena Cruz (Facilities Lead)",
            "current_turn_role": "ADMIN_APPROVER",
            "current_turn_action": "Collect Makati Central Hub RFID turnstile transponder and Locker #18 padlock key.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-19T09:00:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Elena Cruz (Facilities Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "MacBook Air M2 wiped & surrendered"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "PENDING", "summary": "Awaiting physical surrender of Locker #18 key"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Waiting for Admin completion"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting clearance stages"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Angela Soriano (Employee)",
                    "date": "2026-09-19 09:00 AM",
                    "status": "COMPLETED",
                    "details": "Clearance form submitted via Lark Form for Makati Central Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IT Hardware Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-19 02:00 PM",
                    "status": "COMPLETED",
                    "details": "Apple MacBook Air M2 & charger surrendered and wiped cleanly.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Physical Key Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-20 10:00 AM",
                    "status": "IN_PROGRESS",
                    "details": "Waiting on employee to deposit Locker #18 padlock key at security desk.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "Pending Turn",
                    "status": "PENDING",
                    "details": "Will initiate once Facilities confirms key surrender.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to BPI account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-301",
                    "author": "Alex Tan",
                    "role": "IT_APPROVER",
                    "text": "MacBook Air M2 diagnostics 100% clean. Passed to Facilities.",
                    "timestamp": "2026-09-19T14:15:00Z"
                },
                {
                    "id": "cmt-302",
                    "author": "Angela Soriano",
                    "role": "REQUESTER",
                    "text": "Hi Ms. Elena, I left Locker #18 padlock key with the 5th floor receptionist today.",
                    "timestamp": "2026-09-20T10:30:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-004",
            "employee_name": "Rafael Tan",
            "employee_id": "EMP-55219",
            "department": "E-Commerce Fulfillment",
            "company": "CMG Distribution Corp.",
            "unit_channel": "E-Commerce Fulfillment",
            "job_level": "Senior Associate",
            "branch": "Cebu Distribution Center",
            "date_hired": "2022-11-01",
            "eoc_date": "2026-09-24",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_2_FINANCE",
            "stage_name": "Stage 2: Finance & Payroll Audit",
            "stage_step": 2,
            "current_turn_node": "FINANCE",
            "current_turn_name": "Roberto Ong (Finance Lead)",
            "current_turn_role": "FINANCE_APPROVER",
            "current_turn_action": "Audit pro-rated September salary (₱36,500.00) and accrued 13th month bonus.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-18T10:15:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "Zebra barcode scanner surrendered"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Safety boots & uniform returned"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Auditing payroll ledger accruals"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting Finance completion"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Rafael Tan (Employee)",
                    "date": "2026-09-18 10:15 AM",
                    "status": "COMPLETED",
                    "details": "Clearance form lodged for Cebu Fulfillment Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "Warehouse Equipment Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-18 01:00 PM",
                    "status": "COMPLETED",
                    "details": "Zebra handheld inventory scanner S/N ZB-8812 surrendered and verified.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Safety Equipment",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-19 11:00 AM",
                    "status": "COMPLETED",
                    "details": "Warehouse locker cleared; steel-toe boots & hi-vis vest received.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Ledger Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-20 09:30 AM",
                    "status": "IN_PROGRESS",
                    "details": "Auditing pro-rated September earnings & 13th month accrual.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to UnionBank account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-401",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "Computation sheet generated. Auditing shift differential and overtime adjustments.",
                    "timestamp": "2026-09-20T09:45:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-005",
            "employee_name": "Beatriz Ramos",
            "employee_id": "EMP-61298",
            "department": "Human Resources",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Specialist / Professional",
            "branch": "Taguig HQ - 24th Floor",
            "date_hired": "2021-08-16",
            "eoc_date": "2026-09-26",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_2_FINANCE",
            "stage_name": "Stage 2: Finance & Payroll Audit",
            "stage_step": 2,
            "current_turn_node": "FINANCE",
            "current_turn_name": "Roberto Ong (Finance Lead)",
            "current_turn_role": "FINANCE_APPROVER",
            "current_turn_action": "Reconcile tax withholding (BIR Form 2316) and vacation leave monetization balance.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-17T14:20:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "HRIS super-admin access disabled"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Office pedestal key returned"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Reconciling BIR 2316 and leave monetization"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting Finance completion"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Beatriz Ramos (Employee)",
                    "date": "2026-09-17 02:20 PM",
                    "status": "COMPLETED",
                    "details": "Clearance form lodged for Taguig Corporate HQ.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IAM & HRIS System Access Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-17 04:30 PM",
                    "status": "COMPLETED",
                    "details": "HRIS super-admin permissions revoked. Dell Latitude laptop wiped.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Office Pedestal Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-18 10:00 AM",
                    "status": "COMPLETED",
                    "details": "Pedestal keys returned, parking tag cleared.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Tax & Leave Monetization Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-19 01:00 PM",
                    "status": "IN_PROGRESS",
                    "details": "Auditing 8.5 unused vacation leave days monetization (₱14,200.00).",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to BDO account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-501",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "BIR 2316 annualized tax refund computed at ₱3,450.00. Added to final pay ledger.",
                    "timestamp": "2026-09-19T14:00:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-006",
            "employee_name": "Gabriel Mendoza",
            "employee_id": "EMP-44910",
            "department": "Logistics & Supply Chain",
            "company": "CMG Logistics Philippines",
            "unit_channel": "Regional Logistics Hub",
            "job_level": "Team Lead",
            "branch": "Davao Regional Hub",
            "date_hired": "2023-02-01",
            "eoc_date": "2026-09-28",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_1_ASSET",
            "stage_name": "Stage 1: Asset Hand-Off & Turnover",
            "stage_step": 1,
            "current_turn_node": "ADMIN",
            "current_turn_name": "Elena Cruz (Facilities Lead)",
            "current_turn_role": "ADMIN_APPROVER",
            "current_turn_action": "Inspect Davao hub warehouse keys surrender and locker turnover.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-19T11:00:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Elena Cruz (Facilities Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "No company IT assets issued"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "PENDING", "summary": "Physical locker #09 turnover pending"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Awaiting facilities clearance"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting preliminary stages"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Gabriel Mendoza (Employee)",
                    "date": "2026-09-19 11:00 AM",
                    "status": "COMPLETED",
                    "details": "Resignation clearance lodged for Davao Logistics Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IT Account Deactivation",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-19 01:30 PM",
                    "status": "COMPLETED",
                    "details": "WMS mobile scanner user deactivated. No hardware liability.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Davao Hub Facilities Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-20 11:30 AM",
                    "status": "IN_PROGRESS",
                    "details": "Locker #09 physical inspection scheduled with local depot admin.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "Pending Turn",
                    "status": "PENDING",
                    "details": "Payroll calculation queued.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Disbursement pending through Security Bank.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-601",
                    "author": "Elena Cruz",
                    "role": "ADMIN_APPROVER",
                    "text": "Davao depot admin confirmed locker #09 contents inspected. Awaiting final gate pass.",
                    "timestamp": "2026-09-20T11:45:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },

        # =====================================================================
        # 5 FOR REVIEW / FLAGGED TESTER ACCOUNTS (Discrepancy / Action Needed)
        # =====================================================================
        {
            "dossier_id": "DOS-2026-002",
            "employee_name": "Maria Clara Santos",
            "employee_id": "EMP-10294",
            "department": "Finance & Accounting",
            "company": "CMG Retail Inc.",
            "unit_channel": "Retail Stores Network",
            "job_level": "Team Lead",
            "branch": "Makati Central Hub",
            "date_hired": "2020-06-01",
            "eoc_date": "2026-09-15",
            "employee_status": "Regular",
            "reason_for_separation": "End of Contract",
            "with_clearance_already": "Yes",
            "category": "FOR_REVIEW",
            "current_stage": "STAGE_2_FINANCE",
            "stage_name": "Stage 2: Finance & Payroll Audit",
            "stage_step": 2,
            "current_turn_node": "FINANCE",
            "current_turn_name": "Roberto Ong (Finance Lead)",
            "current_turn_role": "FINANCE_APPROVER",
            "current_turn_action": "Discrepancy: ₱3,500 variance between Quitclaim draft (₱52,000) and computed payroll (₱48,500). Eligible for split escrow release.",
            "overall_status": "FLAGGED",
            "submitted_at": "2026-09-17T11:20:00Z",
            "sample_file": "quit_claim_mismatch.pdf",
            "sample_type": "QUIT_CLAIM",
            "ai_flags_count": 2,
            "flags_summary": ["FLAG_AMOUNT_MISMATCH", "FLAG_SIGNATURE_ABSENT"],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "ThinkPad & IAM access revoked"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Store keys surrendered"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "FLAGGED", "summary": "₱3,500 Quitclaim vs Payroll Ledger disparity"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting Finance audit resolution"}
            },
            "escrow_details": {
                "undisputed_amount": 48500.0,
                "escrow_amount": 3500.0,
                "reason": "Disputed adapter deduction: Quitclaim stated amount (₱52,000) vs Computed Final Pay (₱48,500)",
                "status": "PENDING",
                "active": False
            },
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Maria Clara Santos (Employee)",
                    "date": "2026-09-17 11:20 AM",
                    "status": "COMPLETED",
                    "details": "End of Contract clearance lodged via Lark Form for Makati Central Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IT Hardware & Cloud Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-17 03:00 PM",
                    "status": "COMPLETED",
                    "details": "ThinkPad X1 surrendered and inspected. Cloud ERP and IAM access revoked.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Store Keys Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-18 09:30 AM",
                    "status": "COMPLETED",
                    "details": "Office Locker #12 and Makati Central Hub physical store keys surrendered.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-18 02:15 PM",
                    "status": "IN_PROGRESS",
                    "details": "Quitclaim stated amount (₱52,000.00) vs Computed Final Pay (₱48,500.00) has ₱3,500 variance under review.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "Quit Claim & Waiver Sign-Off",
                    "actor": "Maria Clara Santos (Employee)",
                    "date": "Pending Revision",
                    "status": "PENDING",
                    "details": "Awaiting alignment on ₱3,500 variance or split escrow disbursement.",
                    "icon": "fa-signature"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Awaiting Finance audit resolution before final payout execution.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-201",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "Variance of ₱3,500 found between Quitclaim draft (₱52,000) and computed payroll (₱48,500). Eligible for split escrow release.",
                    "timestamp": "2026-09-18T14:30:00Z"
                },
                {
                    "id": "cmt-202",
                    "author": "Grace Diaz",
                    "role": "HR_APPROVER",
                    "text": "Split escrow option ready to disburse ₱48,500.00 immediately to Maria Clara to prevent DOLE 30-day compliance delay.",
                    "timestamp": "2026-09-18T16:00:00Z"
                },
                {
                    "id": "cmt-203",
                    "author": "Maria Clara Santos",
                    "role": "REQUESTER",
                    "text": "Agreeing to the split escrow release of ₱48,500.00 while Finance and HR resolve the ₱3,500 adapter dispute.",
                    "timestamp": "2026-09-18T16:30:00Z"
                }
            ],
            "docs": [
                {"title": "Quit Claim & Waiver", "file": "quit_claim_mismatch.pdf", "type": "QUIT_CLAIM", "has_flags": True},
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-007",
            "employee_name": "Pedro Penduko",
            "employee_id": "EMP-88419",
            "department": "Logistics & Supply Chain",
            "company": "CMG Distribution Corp.",
            "unit_channel": "Logistics Hub",
            "job_level": "Rank & File",
            "branch": "Cebu Distribution Center",
            "date_hired": "2023-01-10",
            "eoc_date": "2026-09-30",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "No",
            "category": "FOR_REVIEW",
            "current_stage": "STAGE_3_QUITCLAIM",
            "stage_name": "Stage 3: Quit Claim & Waiver",
            "stage_step": 3,
            "current_turn_node": "EMPLOYEE",
            "current_turn_name": "Pedro Penduko (Employee)",
            "current_turn_role": "REQUESTER",
            "current_turn_action": "Action Needed from Employee: Re-upload full 11-digit GCash/Bank screenshot (current proof truncated to 6 digits).",
            "overall_status": "FLAGGED",
            "submitted_at": "2026-09-19T14:45:00Z",
            "sample_file": "bank_bad_format.png",
            "sample_type": "BANK_ENROLLMENT",
            "ai_flags_count": 1,
            "flags_summary": ["FLAG_FORMAT_MISMATCH"],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "No IT assets issued"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Safety gear & uniform returned"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "FLAGGED", "summary": "Truncated bank account number (091712)"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting bank proof update"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Pedro Penduko (Employee)",
                    "date": "2026-09-19 02:45 PM",
                    "status": "COMPLETED",
                    "details": "Resignation clearance lodged via Lark Form for Cebu Distribution Center.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IT Access Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-19 04:00 PM",
                    "status": "COMPLETED",
                    "details": "No IT laptop issued; WMS mobile account access deactivated.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Uniform Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-20 10:00 AM",
                    "status": "COMPLETED",
                    "details": "Safety vest, steel-toe boots, and Cebu Hub turnstile RFID returned.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-20 01:15 PM",
                    "status": "IN_PROGRESS",
                    "details": "Payroll computed (₱24,800.00). Bank enrollment account number (091712) truncated; proof upload requested.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "Quit Claim & Bank Verification",
                    "actor": "Pedro Penduko (Employee)",
                    "date": "Pending Bank Proof",
                    "status": "PENDING",
                    "details": "Awaiting valid full 11-digit GCash/Bank screenshot from employee.",
                    "icon": "fa-signature"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Pending verified disbursement target.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-701",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "GCash screenshot is cut off showing only 6 digits (091712). Please upload an uncropped screenshot.",
                    "timestamp": "2026-09-20T13:20:00Z"
                },
                {
                    "id": "cmt-702",
                    "author": "Pedro Penduko",
                    "role": "REQUESTER",
                    "text": "Noted Sir Roberto, uploading the full GCash account profile right away.",
                    "timestamp": "2026-09-20T14:00:00Z"
                }
            ],
            "docs": [
                {"title": "Bank / E-Wallet Proof", "file": "bank_bad_format.png", "type": "BANK_ENROLLMENT", "has_flags": True},
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-008",
            "employee_name": "Antonio Luna",
            "employee_id": "EMP-38491",
            "department": "Operations Management",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Manager",
            "branch": "Taguig HQ - 24th Floor",
            "date_hired": "2019-10-15",
            "eoc_date": "2026-09-18",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "FOR_REVIEW",
            "current_stage": "STAGE_1_ASSET",
            "stage_name": "Stage 1: Asset Hand-Off & Turnover",
            "stage_step": 1,
            "current_turn_node": "IT",
            "current_turn_name": "Alex Tan (IT Clearance Lead)",
            "current_turn_role": "IT_APPROVER",
            "current_turn_action": "Action Needed from IT: MacBook Pro 16\" surrendered but 85W MagSafe 3 charger and USB-C cable missing (₱3,200 payroll adjustment pending approval).",
            "overall_status": "FLAGGED",
            "submitted_at": "2026-09-18T08:00:00Z",
            "sample_file": "clearance_missing_it.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 1,
            "flags_summary": ["FLAG_ACCOUNTABILITY_NOTED"],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Alex Tan (IT Clearance Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "FLAGGED", "summary": "MacBook Pro returned without 85W MagSafe charger"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Taguig basement parking transponder returned"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Awaiting charger deduction clearance"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting IT resolution"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Antonio Luna (Employee)",
                    "date": "2026-09-18 08:00 AM",
                    "status": "COMPLETED",
                    "details": "Managerial clearance submitted for Taguig HQ Operations.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "Laptop Hardware Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-18 10:30 AM",
                    "status": "IN_PROGRESS",
                    "details": "MacBook Pro 16\" (M2 Max) surrendered. Charger absent; replacement cost of ₱3,200 noted for deduction.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Parking Tag Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-18 02:00 PM",
                    "status": "COMPLETED",
                    "details": "Executive basement parking transponder tag surrendered.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "Pending Turn",
                    "status": "PENDING",
                    "details": "Will execute once charger deduction is agreed upon.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final release to BPI bank account.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-801",
                    "author": "Alex Tan",
                    "role": "IT_APPROVER",
                    "text": "MacBook Pro M2 Max body in mint condition. 85W MagSafe charger was not included. Standard deduction is ₱3,200.",
                    "timestamp": "2026-09-18T11:00:00Z"
                },
                {
                    "id": "cmt-802",
                    "author": "Antonio Luna",
                    "role": "REQUESTER",
                    "text": "I may have left the charger at our Cebu branch office. If not found by Monday, please proceed with the deduction.",
                    "timestamp": "2026-09-18T13:45:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_missing_it.pdf", "type": "CLEARANCE_SHEET", "has_flags": True},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-009",
            "employee_name": "Teresa Magbanua",
            "employee_id": "EMP-27411",
            "department": "Retail Operations",
            "company": "CMG Retail Inc.",
            "unit_channel": "Retail Stores Network",
            "job_level": "Store Manager",
            "branch": "Iloilo Branch Hub",
            "date_hired": "2021-05-18",
            "eoc_date": "2026-09-20",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "FOR_REVIEW",
            "current_stage": "STAGE_2_FINANCE",
            "stage_name": "Stage 2: Finance & Payroll Audit",
            "stage_step": 2,
            "current_turn_node": "FINANCE",
            "current_turn_name": "Roberto Ong (Finance Lead)",
            "current_turn_role": "FINANCE_APPROVER",
            "current_turn_action": "Action Needed from Finance: Unliquidated branch store petty cash advance (₱8,500.00) requires liquidation receipts or payroll offset.",
            "overall_status": "FLAGGED",
            "submitted_at": "2026-09-19T10:00:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 1,
            "flags_summary": ["FLAG_ACCOUNTABILITY_NOTED"],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "Store POS supervisor privileges revoked"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Iloilo store safe combination surrendered"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "FLAGGED", "summary": "₱8,500 unliquidated store petty cash advance"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting Finance liquidation"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Teresa Magbanua (Employee)",
                    "date": "2026-09-19 10:00 AM",
                    "status": "COMPLETED",
                    "details": "Clearance form submitted for Iloilo Retail Branch.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "POS Account Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-19 11:30 AM",
                    "status": "COMPLETED",
                    "details": "POS cashier overrides and inventory tablets turned over.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Store Keys & Safe Combination",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-19 03:00 PM",
                    "status": "COMPLETED",
                    "details": "Store keys, alarm PIN, and safe lock combo transferred to incoming OIC.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Petty Cash Reconciliation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-20 09:00 AM",
                    "status": "IN_PROGRESS",
                    "details": "₱8,500.00 emergency store maintenance cash advance outstanding since Aug 28.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to BDO account.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-901",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "Please provide official receipts for the ₱8,500 store aircon repair, or we will offset it against your 13th month pay.",
                    "timestamp": "2026-09-20T09:15:00Z"
                },
                {
                    "id": "cmt-902",
                    "author": "Teresa Magbanua",
                    "role": "REQUESTER",
                    "text": "I have the aircon repair OR and supplier voucher. Uploading scanned PDF now.",
                    "timestamp": "2026-09-20T11:00:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": True},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-010",
            "employee_name": "Emilio Aguinaldo",
            "employee_id": "EMP-71932",
            "department": "Legal & Governance",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Senior Legal Officer",
            "branch": "Taguig HQ - 24th Floor",
            "date_hired": "2020-03-01",
            "eoc_date": "2026-09-19",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "FOR_REVIEW",
            "current_stage": "STAGE_3_QUITCLAIM",
            "stage_name": "Stage 3: Quit Claim & Waiver",
            "stage_step": 3,
            "current_turn_node": "EMPLOYEE",
            "current_turn_name": "Emilio Aguinaldo (Employee)",
            "current_turn_role": "REQUESTER",
            "current_turn_action": "Action Needed from Employee: Quit Claim & Waiver document lacks notary dry seal and witness signature page.",
            "overall_status": "FLAGGED",
            "submitted_at": "2026-09-18T16:00:00Z",
            "sample_file": "quit_claim_mismatch.pdf",
            "sample_type": "QUIT_CLAIM",
            "ai_flags_count": 1,
            "flags_summary": ["FLAG_SIGNATURE_ABSENT"],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Grace Diaz (HR Operations Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "Legal document repository access revoked"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Taguig office keys & badge returned"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "CLEARED", "summary": "Final ledger balanced at ₱84,200.00"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "FLAGGED", "summary": "Quitclaim requires notary seal & signatures"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Emilio Aguinaldo (Employee)",
                    "date": "2026-09-18 04:00 PM",
                    "status": "COMPLETED",
                    "details": "Legal resignation clearance lodged for Taguig HQ.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "Legal Vault Access Revocation",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-18 05:00 PM",
                    "status": "COMPLETED",
                    "details": "Secured corporate contracts drive and e-discovery tools wiped.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Law Library Key Surrender",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-19 09:30 AM",
                    "status": "COMPLETED",
                    "details": "Corporate Law Library keys and 24th floor turnstile tag surrendered.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Executive Payroll Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-19 02:00 PM",
                    "status": "COMPLETED",
                    "details": "Final net pay audited at ₱84,200.00. Zero company liabilities.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "Notarized Quit Claim & Waiver",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "2026-09-20 10:00 AM",
                    "status": "IN_PROGRESS",
                    "details": "Uploaded document missing Page 2 Notarial Acknowledgment seal.",
                    "icon": "fa-signature"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to Metrobank account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-1001",
                    "author": "Grace Diaz",
                    "role": "HR_APPROVER",
                    "text": "Atty. Emilio, page 2 of the Quitclaim PDF was scanned without the notary public seal and witness signatures. Please upload complete copy.",
                    "timestamp": "2026-09-20T10:15:00Z"
                },
                {
                    "id": "cmt-1002",
                    "author": "Emilio Aguinaldo",
                    "role": "REQUESTER",
                    "text": "Apologies, scanner skipped page 2. I have the notarized original right here and am re-uploading.",
                    "timestamp": "2026-09-20T11:20:00Z"
                }
            ],
            "docs": [
                {"title": "Quit Claim & Waiver", "file": "quit_claim_mismatch.pdf", "type": "QUIT_CLAIM", "has_flags": True},
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },

        # =====================================================================
        # 5 READY FOR RELEASE TESTER ACCOUNTS (All 4 Nodes Cleared · Ready to Release)
        # =====================================================================
        {
            "dossier_id": "DOS-2026-011",
            "employee_name": "Elena Cruz",
            "employee_id": "EMP-77102",
            "department": "Retail Operations",
            "company": "CMG Retail Inc.",
            "unit_channel": "Retail Stores Network",
            "job_level": "Junior Associate",
            "branch": "Davao Regional Hub",
            "date_hired": "2023-08-01",
            "eoc_date": "2026-09-25",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "Yes",
            "category": "FOR_RELEASE",
            "current_stage": "STAGE_4_HR_RELEASE",
            "stage_name": "Stage 4: HR Final Release & COE",
            "stage_step": 4,
            "current_turn_node": "HR",
            "current_turn_name": "Grace Diaz (HR Operations Lead)",
            "current_turn_role": "HR_APPROVER",
            "current_turn_action": "All 4 departments cleared! Ready to execute final pay release (₱38,200.00 via BDO) and deliver digital COE.",
            "overall_status": "CLEARED",
            "submitted_at": "2026-09-20T09:10:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Grace Diaz (HR Operations Manager)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "POS credentials revoked"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Store keys surrendered"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "CLEARED", "summary": "Final computation balanced (₱38,200.00)"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "CLEARED", "summary": "COE approved & BDO disbursement authorized"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Elena Cruz (Employee)",
                    "date": "2026-09-20 09:10 AM",
                    "status": "COMPLETED",
                    "details": "Resignation clearance lodged via Lark Form for Davao Regional Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IT Hardware Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-20 11:00 AM",
                    "status": "COMPLETED",
                    "details": "POS inventory tablet returned and cleared.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Store Keys Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-20 01:00 PM",
                    "status": "COMPLETED",
                    "details": "Davao branch store keys and safe lock combination surrendered.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-20 03:00 PM",
                    "status": "COMPLETED",
                    "details": "All deductions zeroed. Final pay ₱38,200.00 balanced.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "Quit Claim & Waiver Sign-Off",
                    "actor": "Elena Cruz (Employee)",
                    "date": "2026-09-20 04:30 PM",
                    "status": "COMPLETED",
                    "details": "Notarized Quit Claim & Waiver signed and validated.",
                    "icon": "fa-signature"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "2026-09-20 05:00 PM",
                    "status": "COMPLETED",
                    "details": "Ready for BDO payout execution and automated digital COE transmission.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-1101",
                    "author": "Grace Diaz",
                    "role": "HR_APPROVER",
                    "text": "100% completed clearance with 0 AI flags. Ready for batch DOLE 30-day payout execution.",
                    "timestamp": "2026-09-20T17:05:00Z"
                },
                {
                    "id": "cmt-1102",
                    "author": "Elena Cruz",
                    "role": "REQUESTER",
                    "text": "Thank you so much to HR, IT, and Admin teams for the fast turnaround!",
                    "timestamp": "2026-09-20T17:15:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-012",
            "employee_name": "Jose Rizal",
            "employee_id": "EMP-99101",
            "department": "Design & Brand Experience",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Specialist / Professional",
            "branch": "Taguig HQ - 24th Floor",
            "date_hired": "2021-02-15",
            "eoc_date": "2026-09-21",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "Yes",
            "category": "FOR_RELEASE",
            "current_stage": "STAGE_4_HR_RELEASE",
            "stage_name": "Stage 4: HR Final Release & COE",
            "stage_step": 4,
            "current_turn_node": "HR",
            "current_turn_name": "Grace Diaz (HR Operations Lead)",
            "current_turn_role": "HR_APPROVER",
            "current_turn_action": "All 4 departments cleared! Ready to execute final pay release (₱72,400.00 via BPI) and deliver digital COE.",
            "overall_status": "CLEARED",
            "submitted_at": "2026-09-19T08:30:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Grace Diaz (HR Operations Manager)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "iMac 27\" & Wacom tablet returned"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Design studio RFID surrendered"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "CLEARED", "summary": "Final computation audited (₱72,400.00)"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "CLEARED", "summary": "COE approved & BPI disbursement authorized"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Jose Rizal (Employee)",
                    "date": "2026-09-19 08:30 AM",
                    "status": "COMPLETED",
                    "details": "Clearance lodged for Design Studio.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "Creative Hardware Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-19 11:30 AM",
                    "status": "COMPLETED",
                    "details": "Apple iMac 27\", Magic Trackpad, and Wacom Cintiq inspected and cleared.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Studio Access & Locker",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-19 02:00 PM",
                    "status": "COMPLETED",
                    "details": "Studio key and locker #04 padlock surrendered.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance Ledger Verification",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-20 10:00 AM",
                    "status": "COMPLETED",
                    "details": "Final pay ledger balanced at ₱72,400.00.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "2026-09-20 03:00 PM",
                    "status": "COMPLETED",
                    "details": "Direct credit scheduled to BPI account. COE generated.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-1201",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "BPI bank details verified. Final pay net amount: ₱72,400.00.",
                    "timestamp": "2026-09-20T10:15:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-013",
            "employee_name": "Melchora Aquino",
            "employee_id": "EMP-41829",
            "department": "Customer Service",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Specialist / Professional",
            "branch": "Makati Central Hub",
            "date_hired": "2022-06-15",
            "eoc_date": "2026-09-23",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "Yes",
            "category": "FOR_RELEASE",
            "current_stage": "STAGE_4_HR_RELEASE",
            "stage_name": "Stage 4: HR Final Release & COE",
            "stage_step": 4,
            "current_turn_node": "HR",
            "current_turn_name": "Grace Diaz (HR Operations Lead)",
            "current_turn_role": "HR_APPROVER",
            "current_turn_action": "All 4 departments cleared! Ready to credit final pay (₱45,600.00 via GCash 0917-555-1234) and deliver digital COE.",
            "overall_status": "CLEARED",
            "submitted_at": "2026-09-19T13:00:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Grace Diaz (HR Operations Manager)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "Zendesk & Plantronics headset returned"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Makati locker surrendered"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "CLEARED", "summary": "Final pay audited (₱45,600.00)"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "CLEARED", "summary": "COE approved & GCash payout authorized"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Melchora Aquino (Employee)",
                    "date": "2026-09-19 01:00 PM",
                    "status": "COMPLETED",
                    "details": "Resignation clearance submitted for Makati CS Department.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "Call Center Headset Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-19 03:30 PM",
                    "status": "COMPLETED",
                    "details": "Noise-cancelling USB headset and softphone extension revoked.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Locker Clearance",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-20 09:00 AM",
                    "status": "COMPLETED",
                    "details": "Makati hub locker #31 returned clean.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-20 11:00 AM",
                    "status": "COMPLETED",
                    "details": "Verified final payout of ₱45,600.00.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "2026-09-20 02:00 PM",
                    "status": "COMPLETED",
                    "details": "GCash verified disbursement ready. COE issued.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-1301",
                    "author": "Melchora Aquino",
                    "role": "REQUESTER",
                    "text": "GCash number confirmed as 0917-555-1234. Thank you team!",
                    "timestamp": "2026-09-20T11:15:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-014",
            "employee_name": "Andres Bonifacio",
            "employee_id": "EMP-31284",
            "department": "Warehouse Operations",
            "company": "CMG Distribution Corp.",
            "unit_channel": "Regional Logistics Hub",
            "job_level": "Team Lead",
            "branch": "Bulacan Distribution Depot",
