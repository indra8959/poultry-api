from flask import Blueprint, request, jsonify
from api_files.utils import duniyape_db
from bson.objectid import ObjectId
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from api_files.duniyape.staff import staff_bp
from api_files.duniyape.trade import trade_bp
from api_files.duniyape.awsfile import aws_bp

duniyape_bp = Blueprint("duniyape_accounting", __name__)





duniyape_bp.register_blueprint(staff_bp, url_prefix="/staff")
duniyape_bp.register_blueprint(trade_bp, url_prefix="/trade")
duniyape_bp.register_blueprint(aws_bp, url_prefix="/aws")

vouchers = duniyape_db["vouchers"] 
groups_collection = duniyape_db["groups"] 
subgroups_collection = duniyape_db["subgroups"] 
ledgers_collection = duniyape_db["ledgers"] 


@duniyape_bp.route("/payment_voucher", methods=["POST"])
def payment_voucher():
    try:
        data = request.json

        narration = data.get('narration')
        date = data.get("date")
        amt = data.get("amount")
        entries = data.get("entries")
        voucher_mode = data.get('voucher_mode', '')

        # ✅ Handle date safely (string + ISO + fallback)
        if isinstance(date, str):
            if "T" in date:
                # ISO format (from frontend toISOString)
                voucher_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                voucher_date = voucher_date.astimezone(ZoneInfo("Asia/Kolkata"))
            else:
                # YYYY-MM-DD
                voucher_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            voucher_date = datetime.now(ZoneInfo("Asia/Kolkata"))

        # ✅ Normalize date (important for daily count)
        start = datetime(voucher_date.year, voucher_date.month, voucher_date.day)
        end = start + timedelta(days=1)

        date_str = start.strftime("%Y-%m-%d")

        count_txn = vouchers.count_documents({})

        count = vouchers.count_documents({
            "voucher_type": "Payment",
            "voucher_mode": voucher_mode,
            "date": {"$gte": start, "$lt": end}
        })

        # ✅ Clean prefix logic
        prefix = "B" if voucher_mode == "Bank" else "C"
        voucher_number = f"{prefix}PV-{date_str}-{count + 1}"

        voucher = {
            "voucher_number": voucher_number,
            "voucher_type": 'Payment',
            "voucher_mode": voucher_mode,
            "txn": count_txn + 1,
            "from_id": "admin",
            "date": start,  # ✅ always normalized datetime
            "narration": narration,
            "amount": float(amt),
            "entries": entries,
            "created_by": "admin",
            "created_at": datetime.now(ZoneInfo("Asia/Kolkata"))
        }

        vouchers.insert_one(voucher)

        return jsonify({
            "status": "ok",
            "voucherCode": voucher_number,
            "txn": count_txn + 1
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    





@duniyape_bp.route("/receipt_voucher", methods=["POST"])
def receipt_voucher():
    try:
        data = request.json

        narration = data.get('narration')
        date = data.get("date")
        amt = data.get("amount")
        entries = data.get("entries")
        voucher_mode = data.get('voucher_mode', '')

        # ✅ Handle date properly
        if isinstance(date, str):
            if "T" in date:
                # ISO format
                voucher_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                voucher_date = voucher_date.astimezone(ZoneInfo("Asia/Kolkata"))
            else:
                # YYYY-MM-DD
                voucher_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            voucher_date = datetime.now(ZoneInfo("Asia/Kolkata"))

        # ✅ Normalize date (important)
        start = datetime(voucher_date.year, voucher_date.month, voucher_date.day)
        end = start + timedelta(days=1)

        date_str = start.strftime("%Y-%m-%d")

        count_txn = vouchers.count_documents({})

        count = vouchers.count_documents({
            "voucher_type": "Receipt",
            "voucher_mode": voucher_mode,
            "date": {"$gte": start, "$lt": end}
        })

        # ✅ Clean voucher number
        prefix = "B" if voucher_mode == "Bank" else "C"
        voucher_number = f"{prefix}RV-{date_str}-{count + 1}"

        voucher = {
            "voucher_number": voucher_number,
            "voucher_type": 'Receipt',
            "voucher_mode": voucher_mode,
            "txn": count_txn + 1,
            "from_id": "admin",
            "date": start,  # ✅ always normalized
            "narration": narration,
            "amount": float(amt),
            "entries": entries,
            "created_by": "admin",
            "created_at": datetime.now(ZoneInfo("Asia/Kolkata"))
        }

        vouchers.insert_one(voucher)

        return jsonify({
            "status": "ok",
            "voucherCode": voucher_number,
            "txn": count_txn + 1
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@duniyape_bp.route("/journal_voucher", methods=["POST"])
def journal_voucher():
    try:
        data = request.json

        date = data.get("date")
        narration = data.get('narration')
        amt = data.get("amount")
        entries = data.get("entries")

        # ✅ Handle date safely
        if isinstance(date, str):
            # ISO format (2026-03-20T00:00:00.000Z)
            if "T" in date:
                voucher_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                voucher_date = voucher_date.astimezone(ZoneInfo("Asia/Kolkata"))
            else:
                # simple format (2026-03-20)
                voucher_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            voucher_date = datetime.now(ZoneInfo("Asia/Kolkata"))

        # ✅ Normalize to start of day (important for counting)
        start = datetime(voucher_date.year, voucher_date.month, voucher_date.day)
        end = start + timedelta(days=1)

        date_str = start.strftime("%Y-%m-%d")

        count_txn = vouchers.count_documents({})

        count = vouchers.count_documents({
            "voucher_type": "Journal",
            "voucher_mode": "Journal",
            "date": {"$gte": start, "$lt": end}
        })

        voucher_number = f"JRV-{date_str}-{count + 1}"

        voucher = {
            "voucher_number": voucher_number,
            "voucher_type": 'Journal',
            "voucher_mode": "Journal",
            "txn": count_txn + 1,
            "from_id": "admin",
            "date": start,  # ✅ store normalized date
            "narration": narration,
            "amount": float(amt),
            "entries": entries,
            "created_by": "admin",
            "created_at": datetime.now(ZoneInfo("Asia/Kolkata"))
        }

        vouchers.insert_one(voucher)

        return jsonify({
            "status": "ok",
            "voucherCode": voucher_number,
            "txn": count_txn + 1
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@duniyape_bp.route("/v1/vouchers", methods=["GET"])
def get_vouchers_filtered():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    voucher_type = request.args.get("voucher_type")
    voucher_mode = request.args.get("voucher_mode")

    ist = ZoneInfo("Asia/Kolkata")
    utc = ZoneInfo("UTC")

    query = {}

    # ✅ FIXED DATE FILTER
    if from_date or to_date:
        date_filter = {}

        if from_date:
            start_ist = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=ist)
            date_filter["$gte"] = start_ist.astimezone(utc)

        if to_date:
            end_ist = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=ist)
            end_ist = end_ist.replace(hour=23, minute=59, second=59)
            date_filter["$lte"] = end_ist.astimezone(utc)

        query["date"] = date_filter

    if voucher_type:
        query["voucher_type"] = voucher_type

    if voucher_mode:
        query["voucher_mode"] = voucher_mode

    # ✅ SORT FROM DB (better)
    voucher_main = list(vouchers.find(query).sort("date", -1))

    for item in voucher_main:
        item["_id"] = str(item["_id"])
        item["company"] = "Duniyape"

        if "date" in item:
            item["date"] = item["date"].astimezone(ist).strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(voucher_main)

@duniyape_bp.route('/v1/ledger/<ledger_id>', methods=['GET'])
def get_ledger_entries(ledger_id):
    from_date_str = request.args.get("from")
    to_date_str = request.args.get("to")
    mapped_id = ledger_id

    # Parse dates
    try:
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d") if from_date_str else None
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d") if to_date_str else None
    except:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    # Helper → opening balance calculation
    def calc_opening(cursor, mapped_id):
        total = 0
        for doc in cursor:
            for entry in doc.get("entries", []):
                if entry.get("ledger_id") == mapped_id:
                    total += entry.get("debit", 0) - entry.get("credit", 0)
        return total

    # --- Opening Balance ---
    opening_balance = 0
    if from_date:

        # Duniyape opening balance
        if mapped_id:
            q = {"entries.ledger_id": mapped_id, "date": {"$lt": from_date}}
            opening_balance += calc_opening(vouchers.find(q), mapped_id)

    # --- Build date filter query ---
    def build_query(mapped_id):
        if not mapped_id:
            return None
        q = {"entries.ledger_id": mapped_id}
        if from_date and to_date:
            q["date"] = {"$gte": from_date, "$lte": to_date}
        elif from_date:
            q["date"] = {"$gte": from_date}
        elif to_date:
            q["date"] = {"$lte": to_date}
        return q

    # Current period fetch
    duniyape_cursor = vouchers.find(build_query(mapped_id)) if mapped_id else []

    # Extract entries helper
    def extract_entries(results, company, mapped_id):
        temp = []
        for doc in results:
            for entry in doc.get("entries", []):
                if entry.get("ledger_id") == mapped_id:
                    temp.append({
                        "voucher_number": doc.get("voucher_number"),
                        "voucher_type": doc.get("voucher_type"),
                        "voucher_mode": doc.get("voucher_mode"),
                        "txn": doc.get("txn"),
                        "ledger_id": entry.get("ledger_id"),
                        "ledger_name": entry.get("ledger_name"),
                        "credit": entry.get("credit"),
                        "debit": entry.get("debit"),
                        "narration": entry.get("narration"),
                        "date": doc.get("date"),
                        "company": company,
                        "empId":entry.get("employee_id") if entry.get("employee_id") else ""
                    })
        return temp

    # Merge entries
    all_entries = []
    if mapped_id:
        all_entries += extract_entries(duniyape_cursor, "Duniyape", mapped_id)

    # Sort by date ASC
    all_entries.sort(key=lambda x: x["date"])

    # Final response
    return jsonify({
        "ledger_id": ledger_id,
        "opening_balance": opening_balance,
        "transaction_count": len(all_entries),
        "transactions": all_entries
    })

@duniyape_bp.route('/v1/ledger2/<ledger_id>/<emp_name>', methods=['GET'])
def get_ledger_entries2(ledger_id, emp_name):
    from_date_str = request.args.get("from")
    to_date_str = request.args.get("to")

    # Validate ledger
    # if ledger_id not in get_ledger:
    #     return jsonify({"error": "Invalid ledger_id"}), 400

    mapped_id = ledger_id

    # Parse dates
    try:
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d") if from_date_str else None
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d") if to_date_str else None
    except:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    # Helper → opening balance calc
    # def calc_opening(cursor, mapped_id):
    #     total = 0
    #     for doc in cursor:
    #         for entry in doc.get("entries", []):
    #             if entry.get("ledger_id") == mapped_id:
    #                 total += entry.get("debit", 0) - entry.get("credit", 0)
    #     return total

    def calc_opening(cursor, mapped_id, emp_name):
        total = 0
        for doc in cursor:
            for entry in doc.get("entries", []):
                if entry.get("ledger_id") == mapped_id:
    
                    emp_id = entry.get("employee_id", "")
                    emp_n = entry.get("employee_name", "").lower()
    
                    # ✅ SAME EMPLOYEE FILTER APPLY HERE
                    if emp_name and not (
                        emp_name == emp_id or emp_name.lower() in emp_n
                    ):
                        continue
    
                    total += entry.get("debit", 0) - entry.get("credit", 0)
        return total

    # ---------------- Opening Balance ----------------
    opening_balance = 0
    if from_date:
        if mapped_id:
            q = {"entries.ledger_id": mapped_id, "date": {"$lt": from_date}}
            opening_balance += calc_opening(vouchers.find(q), mapped_id, emp_name)

   
    # ---------------- Build Query ----------------
    def build_query(mapped_id):
        if not mapped_id:
            return None
        q = {"entries.ledger_id": mapped_id}
        if from_date and to_date:
            q["date"] = {"$gte": from_date, "$lte": to_date}
        elif from_date:
            q["date"] = {"$gte": from_date}
        elif to_date:
            q["date"] = {"$lte": to_date}
        return q

    # Fetch current period data
    duniyape_cursor = vouchers.find(build_query(mapped_id)) if mapped_id else []

    # ---------------- Extract Entries with EMPLOYEE FILTER ----------------
    def extract_entries(results, company, mapped_id, emp_name):
        temp = []
        for doc in results:
            for entry in doc.get("entries", []):
                if entry.get("ledger_id") == mapped_id:

                    emp_id = entry.get("employee_id", "")
                    emp_n = entry.get("employee_name", "").lower()

                    # FILTER BY EMPLOYEE
                    if emp_name and not (
                        emp_name == emp_id or emp_name.lower() in emp_n
                    ):
                        continue  # skip if employee does not match

                    temp.append({
                        "voucher_number": doc.get("voucher_number"),
                        "voucher_type": doc.get("voucher_type"),
                        "voucher_mode": doc.get("voucher_mode"),
                        "txn": doc.get("txn"),
                        "ledger_id": entry.get("ledger_id"),
                        "ledger_name": entry.get("ledger_name"),
                        "credit": entry.get("credit"),
                        "debit": entry.get("debit"),
                        "narration": entry.get("narration"),
                        "date": doc.get("date"),
                        "company": company,
                        "employee_id": emp_id,
                        "employee_name": entry.get("employee_name", "")
                    })
        return temp

    # ---------------- Merge all entries ----------------
    all_entries = []

    if mapped_id:
        all_entries += extract_entries(duniyape_cursor, "Duniyape",mapped_id, emp_name)

    # Sort by date ASC
    all_entries.sort(key=lambda x: x["date"])

    # ---------------- Final Response ----------------
    return jsonify({
        "ledger_id": ledger_id,
        "opening_balance": opening_balance,
        "transaction_count": len(all_entries),
        "transactions": all_entries
    })

# ------------------ GROUPS ------------------
@duniyape_bp.route("/groups", methods=["POST"])
def create_or_edit_group():
    try:
        data = request.json

        if "_id" in data and data["_id"]:  # EDIT
            groups_collection.update_one(
                {"_id": ObjectId(data["_id"])},
                {"$set": {
                    "GroupName": data["groupname"],
                    "GroupType": data["grouptype"]
                }}
            )
            return jsonify({"message": "Group updated successfully"}), 200
        else:  # CREATE
            count = groups_collection.count_documents({})
            mcode = f"G{count + 1}"

            new_group = {
                "Code": mcode,
                "GroupName": data["groupname"],
                "GroupType": data["grouptype"]
            }
            inserted = groups_collection.insert_one(new_group)
            new_group["_id"] = str(inserted.inserted_id)

            return jsonify({"message": "Group created successfully", "group": new_group}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@duniyape_bp.route("/groups", methods=["GET"])
def get_all_groups():
    try:
        groups = list(groups_collection.find())
        for g in groups:
            g["_id"] = str(g["_id"])
        return jsonify(groups), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@duniyape_bp.route("/subgroups", methods=["POST"])
def create_or_edit_subgroup():
    try:
        data = request.json

        if not data.get("group_id"):
            return jsonify({"error": "group_id is required"}), 400

        if not data.get("subgroupname"):
            return jsonify({"error": "subgroupname is required"}), 400

        # -------- EDIT --------
        if data.get("_id"):
            subgroups_collection.update_one(
                {"_id": ObjectId(data["_id"])},
                {"$set": {
                    "Group_id": ObjectId(data["group_id"]),
                    "subgroupname": data["subgroupname"]
                }}
            )
            return jsonify({"message": "Subgroup updated successfully"}), 200

        # -------- CREATE --------
        count = subgroups_collection.count_documents({})
        mcode = f"SG{count + 1}"

        subgroups_collection.insert_one({
            "Code": mcode,
            "Group_id": ObjectId(data["group_id"]),
            "subgroupname": data["subgroupname"]
        })

        # 🔥 IMPORTANT: no ObjectId in response
        return jsonify({"message": "Subgroup created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500





@duniyape_bp.route("/subgroups", methods=["GET"])
def get_all_subgroups():
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "groups",
                    "localField": "Group_id",
                    "foreignField": "_id",
                    "as": "group_info"
                }
            },
            {"$unwind": {"path": "$group_info", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "Code": 1,
                    "subgroupname": 1,

                    # 🔥 MOST IMPORTANT FIX
                    "Group_id": {"$toString": "$Group_id"},

                    "GroupName": {"$ifNull": ["$group_info.GroupName", "-"]},
                    "GroupType": {"$ifNull": ["$group_info.GroupType", "-"]}
                }
            }
        ]

        subgroups = list(subgroups_collection.aggregate(pipeline))
        return jsonify(subgroups), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------ LEDGERS ------------------
@duniyape_bp.route("/ledgers", methods=["POST"])
def create_or_edit_ledger():
    try:
        data = request.json

        # -------- VALIDATION --------
        if not data.get("group_id"):
            return jsonify({"error": "group_id is required"}), 400

        if not data.get("ledgername"):
            return jsonify({"error": "ledgername is required"}), 400

        # -------- EDIT --------
        if data.get("_id"):
            ledgers_collection.update_one(
                {"_id": ObjectId(data["_id"])},
                {"$set": {
                    "Group_id": ObjectId(data["group_id"]),
                    "GroupType": data.get("grouptype"),
                    "LedgerName": data["ledgername"],
                    "subgroupname": data.get("subgroupname", "")
                }}
            )
            return jsonify({"message": "Ledger updated successfully"}), 200

        # -------- CREATE --------
        count = ledgers_collection.count_documents({})
        mcode = f"A{count + 1}"

        ledgers_collection.insert_one({
            "Code": mcode,
            "Group_id": ObjectId(data["group_id"]),
            "GroupType": data.get("grouptype"),
            "LedgerName": data["ledgername"],
            "subgroupname": data.get("subgroupname", "")
        })

        # 🔥 IMPORTANT: do NOT return ObjectId
        return jsonify({"message": "Ledger created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@duniyape_bp.route("/ledgers", methods=["GET"])
def get_all_ledgers():
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "groups",
                    "localField": "Group_id",
                    "foreignField": "_id",
                    "as": "group_info"
                }
            },
            {
                "$unwind": {
                    "path": "$group_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "Code": 1,
                    "LedgerName": 1,
                    "subgroupname": 1,

                    # 🔥 CRITICAL FIX
                    "Group_id": {"$toString": "$Group_id"},

                    "GroupName": {"$ifNull": ["$group_info.GroupName", "-"]},
                    "GroupType": {"$ifNull": ["$group_info.GroupType", "-"]}
                }
            }
        ]

        ledgers = list(ledgers_collection.aggregate(pipeline))
        return jsonify(ledgers), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@duniyape_bp.route("/v1/financial-report", methods=["GET"])
def financial_report():
    report_type = request.args.get("report", "trialbalance")
    from_date_str = request.args.get("from")
    to_date_str = request.args.get("to")

    # ---------- 1. Parse Dates ----------
    try:
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d") if from_date_str else None
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d") if to_date_str else None
    except:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    # ---------- 2. Get Ledger Data ----------
    ledgers_data = {l["Code"]: l for l in ledgers_collection.find()}

    # ---------- 3. Trial Balance ----------
    if report_type == "trialbalance":



        
        trial_balance = {}

        for ledger_id in ledgers_data.keys():

            mapped_id = ledger_id

            # ================= OPENING BALANCE =================
            opening_balance = 0

            if from_date:
                pipeline_open = [
                    {
                        "$match": {
                            "entries.ledger_id": mapped_id,
                            "date": {"$lt": from_date}
                        }
                    },
                    {"$unwind": "$entries"},
                    {"$match": {"entries.ledger_id": mapped_id}},
                    {
                        "$group": {
                            "_id": None,
                            "balance": {
                                "$sum": {
                                    "$subtract": ["$entries.debit", "$entries.credit"]
                                }
                            }
                        }
                    }
                ]

                result_open = list(vouchers.aggregate(pipeline_open))
                opening_balance = result_open[0]["balance"] if result_open else 0

            # ================= CURRENT PERIOD =================
            match_query = {"entries.ledger_id": mapped_id}

            if from_date or to_date:
                match_query["date"] = {}
                if from_date:
                    match_query["date"]["$gte"] = from_date
                if to_date:
                    match_query["date"]["$lte"] = to_date

            pipeline_current = [
                {"$match": match_query},
                {"$unwind": "$entries"},
                {"$match": {"entries.ledger_id": mapped_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_debit": {"$sum": "$entries.debit"},
                        "total_credit": {"$sum": "$entries.credit"}
                    }
                }
            ]

            result_current = list(vouchers.aggregate(pipeline_current))

            total_debit = result_current[0]["total_debit"] if result_current else 0
            total_credit = result_current[0]["total_credit"] if result_current else 0

            # ================= META =================
            group_type = ledgers_data.get(ledger_id, {}).get("GroupType", "Unknown")
            ledger_name = ledgers_data.get(ledger_id, {}).get("LedgerName", ledger_id)

            if group_type not in trial_balance:
                trial_balance[group_type] = []

            closing_raw = opening_balance + total_debit - total_credit
            closing_type = "DR" if closing_raw >= 0 else "CR"

            trial_balance[group_type].append({
                "ledger_id": ledger_id,
                "ledger_name": ledger_name,
                "opening_balance": abs(opening_balance),
                "period_debit": total_debit,
                "period_credit": total_credit,
                "closing_balance": abs(closing_raw),
                "closing_type": closing_type
            })

        return jsonify(trial_balance)

    return jsonify({"error": "Invalid report type"}), 400
