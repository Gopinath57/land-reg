import difflib
from models import LandRecord, Document, db

class RecordComparator:
    @staticmethod
    def compare_record_with_document(record_id, document_id):
        record = LandRecord.query.get(record_id)
        document = Document.query.get(document_id)
        if not record or not document:
            return None

        parsed = document.parsed_data
        field_comparisons = []
        total_points = 0
        earned_points = 0
        discrepancy_list = []

        # 1. Owner Name
        doc_owner = parsed.get('owner_name')
        if doc_owner:
            ratio = difflib.SequenceMatcher(None, record.owner_name.lower().strip(), doc_owner.lower().strip()).ratio()
            pts = ratio * 20
            earned_points += pts
            total_points += 20
            match_type = 'MATCH' if ratio >= 0.9 else ('MINOR_MISMATCH' if ratio >= 0.65 else 'CRITICAL_MISMATCH')
            if match_type != 'MATCH':
                discrepancy_list.append(f"Owner Name discrepancy: Registry has \"{record.owner_name}\", Document has \"{doc_owner}\"")
            field_comparisons.append({
                'field': 'Owner Name',
                'record_value': record.owner_name,
                'doc_value': doc_owner,
                'status': match_type,
                'similarity': round(ratio * 100, 1)
            })

        # 2. Khasra Number
        doc_khasra = parsed.get('khasra_number')
        if doc_khasra:
            is_match = (record.khasra_number.strip().lower() == doc_khasra.strip().lower())
            earned_points += 25 if is_match else 0
            total_points += 25
            status = 'MATCH' if is_match else 'CRITICAL_MISMATCH'
            if not is_match:
                discrepancy_list.append(f"Khasra Number mismatch: Registry={record.khasra_number}, Document={doc_khasra}")
            field_comparisons.append({
                'field': 'Khasra Number',
                'record_value': record.khasra_number,
                'doc_value': doc_khasra,
                'status': status,
                'similarity': 100.0 if is_match else 0.0
            })

        # 3. Village
        doc_village = parsed.get('village')
        if doc_village:
            is_match = (record.village.strip().lower() == doc_village.strip().lower())
            earned_points += 15 if is_match else 0
            total_points += 15
            status = 'MATCH' if is_match else 'CRITICAL_MISMATCH'
            if not is_match:
                discrepancy_list.append(f"Village mismatch: Registry={record.village}, Document={doc_village}")
            field_comparisons.append({
                'field': 'Village',
                'record_value': record.village,
                'doc_value': doc_village,
                'status': status,
                'similarity': 100.0 if is_match else 0.0
            })

        # 4. District
        doc_district = parsed.get('district')
        if doc_district:
            is_match = (record.district.strip().lower() == doc_district.strip().lower())
            earned_points += 15 if is_match else 0
            total_points += 15
            status = 'MATCH' if is_match else 'CRITICAL_MISMATCH'
            if not is_match:
                discrepancy_list.append(f"District mismatch: Registry={record.district}, Document={doc_district}")
            field_comparisons.append({
                'field': 'District',
                'record_value': record.district,
                'doc_value': doc_district,
                'status': status,
                'similarity': 100.0 if is_match else 0.0
            })

        # 5. Area in Acres
        doc_area = parsed.get('area_acres')
        if doc_area is not None:
            try:
                doc_a = float(doc_area)
                rec_a = float(record.area_acres)
                diff = abs(rec_a - doc_a)
                total_points += 25
                if diff <= 0.01:
                    status = 'MATCH'
                    earned_points += 25
                elif diff <= 0.15:
                    status = 'MINOR_MISMATCH'
                    earned_points += 12
                    discrepancy_list.append(f"Minor Area difference: Registry={rec_a} Acres, Document={doc_a} Acres (Delta: {round(diff, 2)})")
                else:
                    status = 'CRITICAL_MISMATCH'
                    discrepancy_list.append(f"Critical Area mismatch: Registry={rec_a} Acres vs Document={doc_a} Acres")
                field_comparisons.append({
                    'field': 'Area (Acres)',
                    'record_value': f"{rec_a} Acres",
                    'doc_value': f"{doc_a} Acres",
                    'status': status,
                    'similarity': round(max(0, 100 - (diff / max(rec_a, doc_a, 1)) * 100), 1)
                })
            except (ValueError, TypeError):
                pass

        overall_score = round((earned_points / total_points * 100), 1) if total_points > 0 else 100.0
        has_mismatch = len(discrepancy_list) > 0

        record.mismatch_detected = has_mismatch
        record.mismatch_notes = ' | '.join(discrepancy_list) if has_mismatch else 'Perfect match between Registry and Document.'
        if has_mismatch and record.status not in ['Verified', 'Rejected', 'Flagged Duplicate']:
            record.status = 'Flagged Mismatch'
        db.session.commit()

        return {
            'overall_score': overall_score,
            'has_mismatch': has_mismatch,
            'field_comparisons': field_comparisons,
            'discrepancies': discrepancy_list
        }
