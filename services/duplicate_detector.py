import difflib
from models import LandRecord, db

class DuplicateDetector:
    @staticmethod
    def calculate_string_similarity(str1, str2):
        if not str1 or not str2:
            return 0.0
        s1 = str1.strip().lower()
        s2 = str2.strip().lower()
        if s1 == s2:
            return 100.0
        return round(difflib.SequenceMatcher(None, s1, s2).ratio() * 100, 1)

    @staticmethod
    def scan_record(record_id):
        record = LandRecord.query.get(record_id)
        if not record:
            return {'risk_level': 'None', 'matches': [], 'summary': 'Record not found'}

        candidates = LandRecord.query.filter(LandRecord.id != record.id).all()
        matches = []
        highest_score = 0.0

        for other in candidates:
            score = 0.0
            reasons = []

            if record.khasra_number and other.khasra_number:
                k1 = record.khasra_number.strip().lower()
                k2 = other.khasra_number.strip().lower()
                if k1 == k2 and record.village.lower() == other.village.lower() and record.district.lower() == other.district.lower():
                    score += 95.0
                    reasons.append(f"Exact Khasra duplicate ({record.khasra_number}) in Village {record.village}, District {record.district}")
                elif k1 == k2 and record.district.lower() == other.district.lower():
                    score += 65.0
                    reasons.append(f"Identical Khasra ({record.khasra_number}) in same District {record.district}")

            if record.survey_number and other.survey_number:
                s1 = record.survey_number.strip().lower()
                s2 = other.survey_number.strip().lower()
                if s1 == s2:
                    score += 85.0
                    reasons.append(f"Identical Survey Number ({record.survey_number}) match")

            name_sim = DuplicateDetector.calculate_string_similarity(record.owner_name, other.owner_name)
            if name_sim >= 85.0:
                score += 30.0
                reasons.append(f"High owner name similarity: {name_sim}% (\"{record.owner_name}\" vs \"{other.owner_name}\")")
            elif name_sim >= 70.0 and record.village.lower() == other.village.lower():
                score += 20.0
                reasons.append(f"Partial owner name similarity ({name_sim}%) in same village")

            if record.area_acres and other.area_acres and abs(record.area_acres - other.area_acres) < 0.05:
                if record.village.lower() == other.village.lower():
                    score += 15.0
                    reasons.append(f"Nearly identical parcel size ({record.area_acres} Acres) in same village")

            final_score = min(round(score, 1), 100.0)
            if final_score >= 40.0:
                matches.append({
                    'record_id': other.id,
                    'parcel_id': other.parcel_id,
                    'khasra_number': other.khasra_number,
                    'survey_number': other.survey_number,
                    'owner_name': other.owner_name,
                    'village': other.village,
                    'district': other.district,
                    'status': other.status,
                    'score': final_score,
                    'reasons': reasons
                })
                if final_score > highest_score:
                    highest_score = final_score

        matches.sort(key=lambda x: x['score'], reverse=True)

        risk_level = 'None'
        matched_id = None
        notes = ''

        if highest_score >= 80.0:
            risk_level = 'High'
            matched_id = matches[0]['record_id']
            primary_reason = matches[0]['reasons'][0]
            target_pid = matches[0]['parcel_id']
            notes = f"High collision risk ({highest_score}%) with Parcel {target_pid}: {primary_reason}"
        elif highest_score >= 50.0:
            risk_level = 'Medium'
            matched_id = matches[0]['record_id']
            target_pid = matches[0]['parcel_id']
            notes = f"Moderate overlap risk ({highest_score}%) with Parcel {target_pid}"
        elif highest_score >= 35.0:
            risk_level = 'Low'
            notes = f"Minor similarity ({highest_score}%) detected"

        record.duplicate_risk = risk_level
        record.duplicate_matched_id = matched_id
        record.duplicate_notes = notes
        if risk_level == 'High' and record.status not in ['Verified', 'Rejected']:
            record.status = 'Flagged Duplicate'
        db.session.commit()

        return {
            'risk_level': risk_level,
            'highest_score': highest_score,
            'matches': matches,
            'summary': notes if notes else 'No duplicate collisions detected.'
        }

    @staticmethod
    def scan_all_records():
        records = LandRecord.query.all()
        total_scanned = len(records)
        flagged_count = 0
        for r in records:
            res = DuplicateDetector.scan_record(r.id)
            if res['risk_level'] in ['High', 'Medium']:
                flagged_count += 1
        return {
            'total_scanned': total_scanned,
            'flagged_count': flagged_count
        }
