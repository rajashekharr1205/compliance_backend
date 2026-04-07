import csv
import re
import os

class ComplianceModel:
    """
    Clinical NLP Compliance Model with:
    1. Multi-dataset loading (merges 1000-word + 3000-word datasets)
    2. Stopword normalization (strips filler words, preserves negations)
    3. Synonym augmentation (expands rules with clinical synonyms)
    4. Dual-dictionary matching (exact match on raw + normalized phrases)
    """

    # ── Clinical Synonym Map ──────────────────────────────────────────
    # key = word found in dataset phrases
    # value = list of spoken-language synonyms the patient might actually say
    SYNONYMS = {
        'reduced':     ['manageable', 'better', 'improving', 'subsided', 'decreased', 'less', 'controlled'],
        'pain':        ['discomfort', 'ache', 'hurt', 'hurting', 'sore', 'soreness', 'uncomfortable'],
        'scared':      ['afraid', 'fear', 'fearful', 'anxious', 'nervous', 'worried', 'terrified'],
        'come':        ['visit', 'attend', 'arrive', 'reach', 'go', 'make it'],
        'tomorrow':    ['next day'],
        'cancel':      ['postpone', 'reschedule', 'delay', 'defer', 'skip'],
        'busy':        ['occupied', 'unavailable', 'tied up', 'no time'],
        'medicine':    ['medication', 'tablets', 'pills', 'drugs', 'prescription'],
        'treatment':   ['procedure', 'therapy', 'operation', 'surgery'],
        'dentist':     ['dental', 'clinic', 'doctor', 'hospital'],
        'appointment': ['visit', 'session', 'consultation', 'meeting', 'checkup', 'check up'],
        'bleeding':    ['blood', 'bleed'],
        'swelling':    ['swollen', 'inflammation', 'inflamed', 'puffiness'],
        'worse':       ['worsened', 'worsening', 'deteriorating', 'aggravated', 'bad'],
        'interested':  ['willing', 'keen', 'ready', 'happy to'],
        'feeling':     ['feel', 'felt'],
        'improving':   ['getting better', 'recovering', 'healing'],
        'confirmed':   ['confirm', 'sure', 'certain', 'definitely'],
        'absolutely':  ['definitely', 'certainly', 'surely', 'of course'],
        'maybe':       ['perhaps', 'possibly', 'might', 'probably'],
        'later':       ['sometime', 'after', 'afterward', 'afterwards'],
    }

    # ── Stopwords (filler words stripped from BOTH dataset and transcript) ──
    # CRITICAL: Negations like 'no', 'not', 'never', 'cannot' are EXCLUDED
    # from this set so they are PRESERVED and correctly affect compliance.
    STOPWORDS = frozenset({
        'i', 'me', 'my', 'myself', 'we', 'our', 'you', 'your', 'yours',
        'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their',
        'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
        'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as',
        'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
        'between', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
        'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
        'here', 'there', 'when', 'where', 'why', 'how',
        'all', 'any', 'both', 'each', 'few', 'other',
        'some', 'such', 'own', 'same', 'than',
        'now', 'also', 'still',
        'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might',
        'need', 'must', 'ought',
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
    })

    # ── Phonetic Correction Map ───────────────────────────────────────
    # key = misinterpreted word(s) from STT
    # value = intended word
    PHONETIC_MAP = {
        'this comfort': 'discomfort',
        'aloud':        'allowed',
        'aural':        'oral',
        'site':         'sight',
        's':            'yes',
    }

    # Words that MUST NEVER be stripped — these change compliance meaning
    NEGATIONS = frozenset({
        'no', 'not', 'none', 'never', 'neither', 'nobody', 'nothing',
        'nowhere', 'cannot', 'dont', 'wont', 'cant', 'didnt', 'doesnt',
        'isnt', 'arent', 'wasnt', 'werent', 'hasnt', 'havent', 'hadnt',
        'shouldnt', 'wouldnt', 'couldnt', 'mustnt',
    })

    CATEGORY_SCORES = {
        'High': 10,
        'Acknowledgment': 3,
        'Medium': 5,
        'Low': -10,
        'Symptom': 2,
    }

    def __init__(self, dataset_paths):
        self.phrase_dict = {}      # original phrase -> {category, score}
        self.norm_dict = {}        # normalized phrase -> {category, score, original}
        self.max_phrase_len = 0    # max words in original phrases
        self.max_norm_len = 0      # max words in normalized phrases

        if isinstance(dataset_paths, list):
            for path in dataset_paths:
                self.load_rules(path)
        else:
            self.load_rules(dataset_paths)

        # After loading all raw rules, build normalized + augmented dictionary
        self._build_norm_dict()
        print(f"NLP Engine ready: {len(self.phrase_dict)} raw phrases, "
              f"{len(self.norm_dict)} normalized entries (after synonym expansion). "
              f"Max window: {self.max_norm_len} words.")

    # ──────────────────────────────────────────────────────────────────
    # DATA LOADING
    # ──────────────────────────────────────────────────────────────────

    def load_rules(self, dataset_path):
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset not found at {dataset_path}")
            return

        try:
            with open(dataset_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                headers = reader.fieldnames
                raw_count = 0

                for row in reader:
                    raw_count += 1
                    if 'Category' in headers and 'Phrase' in headers:
                        phrase = row['Phrase'].lower().strip()
                        category = row['Category'].strip()
                        score = self.CATEGORY_SCORES.get(category, 0)
                    elif 'phrase' in headers and 'category' in headers:
                        phrase = row['phrase'].lower().strip()
                        category = row['category'].strip()
                        score = int(row.get('score', self.CATEGORY_SCORES.get(category, 0)))
                    else:
                        continue

                    if not phrase:
                        continue

                    phrase = re.sub(r'[^\w\s]', '', phrase).strip()
                    phrase = re.sub(r'\s+', ' ', phrase)
                    if not phrase:
                        continue

                    # Preserve better information if it already exists
                    new_situation = row.get('situation', row.get('Situation', 'General'))
                    if phrase in self.phrase_dict:
                        old_situation = self.phrase_dict[phrase].get('situation', 'General')
                        if old_situation != 'General' and new_situation == 'General':
                            new_situation = old_situation

                    self.phrase_dict[phrase] = {
                        'category': category,
                        'score': score,
                        'situation': new_situation
                    }

                    word_count = len(phrase.split())
                    if word_count > self.max_phrase_len:
                        self.max_phrase_len = word_count

            print(f"Loaded {len(self.phrase_dict)} unique phrases from {raw_count} rows in {os.path.basename(dataset_path)}")
        except Exception as e:
            print(f"Error loading dataset: {e}")

    # ──────────────────────────────────────────────────────────────────
    # NLP NORMALIZATION ENGINE
    # ──────────────────────────────────────────────────────────────────

    def _normalize(self, text):
        """
        Strips filler stopwords while strictly preserving negations.
        'I will come tomorrow' → 'come tomorrow'
        'I will not come'      → 'not come'
        """
        words = text.lower().split()
        return ' '.join(w for w in words if w not in self.STOPWORDS or w in self.NEGATIONS)

    def _build_norm_dict(self):
        """
        Builds a normalized + synonym-expanded dictionary from raw phrases.

        For each raw phrase:
        1. Normalize it (strip stopwords)
        2. Store normalized → {category, score, original}
        3. Generate synonym expansions and store those too
        """
        for phrase, rule in self.phrase_dict.items():
            norm = self._normalize(phrase)
            if not norm:
                norm = phrase  # fallback: keep original if entirely stopwords

            entry = {
                'category': rule['category'],
                'score': rule['score'],
                'situation': rule.get('situation', 'General'),
                'original': phrase
            }

            # Store normalized form
            if norm not in self.norm_dict:
                self.norm_dict[norm] = entry

            # Track max normalized phrase length
            norm_len = len(norm.split())
            if norm_len > self.max_norm_len:
                self.max_norm_len = norm_len

            # ── Synonym Expansion ──
            # For each word in the phrase, if it has synonyms,
            # generate variant phrases with each synonym substituted
            phrase_words = norm.split()
            for idx, word in enumerate(phrase_words):
                if word in self.SYNONYMS:
                    for syn in self.SYNONYMS[word]:
                        syn_words = list(phrase_words)
                        syn_words[idx] = syn
                        syn_phrase = ' '.join(syn_words)
                        if syn_phrase not in self.norm_dict:
                            self.norm_dict[syn_phrase] = {
                                'category': rule['category'],
                                'score': rule['score'],
                                'situation': rule.get('situation', 'General'),
                                'original': f"{syn_phrase} (~{phrase})"
                            }
                            syn_len = len(syn_words)
                            if syn_len > self.max_norm_len:
                                self.max_norm_len = syn_len

    def _apply_phonetic_corrections(self, text):
        """
        Fixes common speech-to-text misinterpretations (homophones).
        'this comfort' -> 'discomfort'
        'aloud' -> 'allowed'
        """
        # First handle multi-word corrections
        for wrong, right in self.PHONETIC_MAP.items():
            if ' ' in wrong:
                text = re.sub(r'\b' + re.escape(wrong) + r'\b', right, text)
        
        # Then handle single-word corrections
        words = text.split()
        corrected_words = []
        for w in words:
            if w in self.PHONETIC_MAP and ' ' not in w:
                corrected_words.append(self.PHONETIC_MAP[w])
            else:
                corrected_words.append(w)
        
        return ' '.join(corrected_words)

    def preprocess_text(self, text):
        """
        Preprocesses the input text:
        - Convert to lowercase
        - Apply phonetic corrections (STT fixes)
        - Remove punctuation and special characters
        - Normalize whitespace
        """
        text = text.lower()
        # Apply phonetic corrections before removing punctuation in case 'this comfort' has a space
        text = self._apply_phonetic_corrections(text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # ──────────────────────────────────────────────────────────────────
    # CONTEXT-AWARE CATEGORY ADJUSTMENT
    # ──────────────────────────────────────────────────────────────────

    # Conditional/hesitation words that downgrade High → Medium
    CONDITIONALS = frozenset({
        'maybe', 'perhaps', 'possibly', 'probably', 'might',
        'if', 'depends', 'depending', 'uncertain', 'unsure',
    })

    def _apply_context_check(self, words, match_start_pos, category, score):
        """
        Examines the ORIGINAL transcript words surrounding a match to
        detect negation or conditional context that changes compliance meaning.

        Rules:
        1. Negation within 8 words before a High/Medium match → flip to Low
           e.g. "I cannot come for the appointment this week"
           'cannot' is 6 words before 'this week' → flip to Low
        2. Conditional within 4 words before a High match → downgrade to Medium
           e.g. "maybe I will visit" → downgrade 'visit' from High to Medium
        """
        if category not in ('High', 'Medium'):
            return category, score

        # ── Check 1: Negation (wide 8-word lookback) ──
        lookback_start = max(0, match_start_pos - 8)
        context_words = words[lookback_start:match_start_pos]
        has_negation = any(w in self.NEGATIONS for w in context_words)
        if has_negation:
            return 'Low', -10

        # ── Check 2: Conditional (4-word lookback, only for High) ──
        if category == 'High':
            cond_start = max(0, match_start_pos - 4)
            cond_words = words[cond_start:match_start_pos]
            has_conditional = any(w in self.CONDITIONALS for w in cond_words)
            if has_conditional:
                return 'Medium', 5

        return category, score

    # ──────────────────────────────────────────────────────────────────
    # MATCHING ENGINE (Dual-Pass)
    # ──────────────────────────────────────────────────────────────────

    def find_matches(self, words):
        """
        Dual-pass greedy sliding-window matcher:

        Pass 1: Exact match on raw phrase_dict (preserves original behavior)
        Pass 2: Normalize the transcript, match against norm_dict
                 (catches variations like 'can come' → 'come' → matches 'i will come')

        Deduplication ensures no position is matched twice.
        """
        matches = []
        used_positions = set()

        # ── Pass 1: Exact match on raw phrases ──
        i = 0
        n = len(words)
        while i < n:
            matched = False
            max_len = min(self.max_phrase_len, n - i)
            for length in range(max_len, 0, -1):
                candidate = ' '.join(words[i:i + length])
                if candidate in self.phrase_dict:
                    rule = self.phrase_dict[candidate]
                    category = rule['category']
                    score = rule['score']

                    # Apply context checks
                    category, score = self._apply_context_check(
                        words, i, category, score
                    )

                    matches.append({
                        'phrase': candidate,
                        'category': category,
                        'score': score,
                        'situation': rule.get('situation', 'General'),
                        'position': i
                    })
                    for p in range(i, i + length):
                        used_positions.add(p)
                    i += length
                    matched = True
                    break
            if not matched:
                i += 1

        # ── Pass 2: Normalized match on norm_dict ──
        # Normalize the transcript words (strip stopwords, keep negations)
        norm_words = []
        norm_to_orig_pos = []  # maps each norm_word index → original word position
        for idx, w in enumerate(words):
            if w not in self.STOPWORDS or w in self.NEGATIONS:
                norm_words.append(w)
                norm_to_orig_pos.append(idx)

        i = 0
        nn = len(norm_words)
        while i < nn:
            orig_pos = norm_to_orig_pos[i]
            if orig_pos in used_positions:
                i += 1
                continue

            matched = False
            max_len = min(self.max_norm_len, nn - i)
            for length in range(max_len, 0, -1):
                candidate = ' '.join(norm_words[i:i + length])
                if len(candidate) < 2:
                    continue
                if candidate in self.norm_dict:
                    rule = self.norm_dict[candidate]
                    # Check this span doesn't overlap with Pass 1 matches
                    span_positions = [norm_to_orig_pos[j] for j in range(i, i + length)]
                    if any(p in used_positions for p in span_positions):
                        continue

                    category = rule['category']
                    score = rule['score']

                    # Apply context checks using ORIGINAL word positions
                    first_orig_pos = span_positions[0]
                    category, score = self._apply_context_check(
                        words, first_orig_pos, category, score
                    )

                    matches.append({
                        'phrase': rule['original'],
                        'category': category,
                        'score': score,
                        'situation': rule.get('situation', 'General'),
                        'position': orig_pos
                    })
                    for p in span_positions:
                        used_positions.add(p)
                    i += length
                    matched = True
                    break

            if not matched:
                i += 1

        # Sort by position for consistent ordering
        matches.sort(key=lambda m: m['position'])
        return matches

    # ──────────────────────────────────────────────────────────────────
    # SCORING
    # ──────────────────────────────────────────────────────────────────

    def calculate_score(self, matches, total_words):
        """Revised scoring with evidence-density dampening and acknowledgment awareness."""
        if not matches:
            return 0.0

        high_count = sum(1 for m in matches if m['category'] == 'High')
        ack_count = sum(1 for m in matches if m['category'] == 'Acknowledgment')
        medium_count = sum(1 for m in matches if m['category'] == 'Medium')
        low_count = sum(1 for m in matches if m['category'] == 'Low')
        symptom_count = sum(1 for m in matches if m['category'] == 'Symptom')
        total_matches = len(matches)

        total_score = sum(m['score'] for m in matches)
        max_possible = total_matches * 10

        if max_possible == 0:
            return 0.0

        # Base percentage from score ratio
        percentage = ((total_score + max_possible) / (2 * max_possible)) * 100

        # ── Rule 1: Acknowledgment-Only Cap ──
        # If ALL matches are just filler words (okay, yes, hmm, greetings)
        # with NO actual commitment or medical substance, cap severely
        has_commitment = high_count > 0
        has_uncertainty = medium_count > 0
        has_refusal = low_count > 0
        only_acknowledgments = (ack_count == total_matches) or \
                               (ack_count > 0 and not has_commitment and not has_uncertainty and not has_refusal and symptom_count == 0)

        if only_acknowledgments:
            percentage = min(45.0, percentage)

        # ── Rule 2: Acknowledgment + Medium (no High) ──
        # e.g., "I think" (Medium) + "okay" (Ack) -> should NOT be high
        if not has_commitment and not has_refusal:
            if has_uncertainty and ack_count > 0:
                percentage = min(50.0, percentage)
            elif has_uncertainty and ack_count == 0:
                percentage = min(55.0, percentage)

        # ── Rule 3: Require High commitment for >70% ──
        if not has_commitment:
            percentage = min(60.0, percentage)

        # ── Rule 4: Evidence density dampening ──
        # Few matches = less confidence = dampen towards neutral
        if total_matches == 1:
            deviation = percentage - 50.0
            percentage = 50.0 + (deviation * 0.6)
        elif total_matches == 2:
            deviation = percentage - 50.0
            percentage = 50.0 + (deviation * 0.75)

        # ── Rule 5: Short transcript penalty ──
        situations = [m.get('situation', '').lower() for m in matches]
        has_strong_commitment = any(s in ('appointment_commitment', 'treatment_compliance', 'confirmation') 
                                   for s in situations)

        if total_words < 5:
            damp_factor = 0.5 if has_strong_commitment else 0.2
            deviation = percentage - 25.0
            percentage = 25.0 + (deviation * damp_factor)
        elif total_words < 10:
            damp_factor = 0.8 if has_strong_commitment else 0.5
            deviation = percentage - 35.0
            percentage = 35.0 + (deviation * damp_factor)

        # ── Rule 6: Low matches pull score down hard ──
        if has_refusal:
            if high_count == 0:
                # Pure refusal
                percentage = min(25.0, percentage)
            else:
                # Mixed signals: dampen
                percentage = min(45.0, percentage)

        return round(max(0.0, min(100.0, percentage)), 2)

    # ──────────────────────────────────────────────────────────────────
    # MAIN ANALYSIS PIPELINE
    # ──────────────────────────────────────────────────────────────────

    def analyze_conversation(self, text):
        original_text = text
        processed_text = self.preprocess_text(text)
        words = processed_text.split()
        total_words = len(words)

        matches = self.find_matches(words)

        high_count = sum(1 for m in matches if m['category'] == 'High')
        medium_count = sum(1 for m in matches if m['category'] == 'Medium')
        low_count = sum(1 for m in matches if m['category'] == 'Low')
        total_matches = len(matches)

        total_score = sum(m['score'] for m in matches)
        compliance_percentage = self.calculate_score(matches, total_words)

        compliance_percentage = round(max(0.0, min(100.0, compliance_percentage)), 2)

        # Classification
        if total_matches == 0:
            compliance_level = "Inconclusive"
            prediction = "Insufficient data to determine patient intent"
            verdict = "N/A"
        elif compliance_percentage >= 70:
            compliance_level = "High"
            prediction = "Patient will attend the next appointment"
            verdict = "Interested"
        elif compliance_percentage >= 45:
            compliance_level = "Medium"
            prediction = "Patient may attend the next appointment"
            verdict = "Uncertain"
        else:
            compliance_level = "Low"
            prediction = "Patient will not attend the next appointment"
            verdict = "Not Interested"

        return {
            "transcript": original_text,
            "matched_keywords": [m['phrase'] for m in matches],
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "total_matches": total_matches,
            "total_raw_score": total_score,
            "compliance_percentage": float(compliance_percentage),
            "compliance_level": compliance_level,
            "prediction": prediction,
            "verdict": verdict
        }


if __name__ == "__main__":
    dataset_1000 = os.path.join(os.path.dirname(__file__), 'dental_rule_based_dataset_1000.csv')
    dataset_3000 = os.path.join(os.path.dirname(__file__), 'dental_compliance_words_3000.csv')
    dataset_ai = os.path.join(os.path.dirname(__file__), 'dental_compliance_ai_expanded.csv')
    model = ComplianceModel([dataset_1000, dataset_3000, dataset_ai])

    test_texts = [
        # User's real transcript
        "no doctor I do not think I can come tomorrow because what to do . the pain is manageable now and I am not feeling much this comfort and I will see later if the problem becomes worse",
        # Previous test transcript
        "I think the pain is slightly better now doctor but sometimes I still feel some discomfort while eating . maybe I can come for the check up but I need to check my schedule . I will try to visit the clinic next week if possible . I am not completely sure right now but I will confirm later after checking my time .",
        # High compliance
        "Yes doctor I will come tomorrow. Feeling better. Pain reduced.",
        "Okay doctor, I will attend. I will brush twice daily and floss daily.",
        # Medium compliance
        "Maybe next week. I am busy right now but I will check schedule.",
        "I think I might come, probably tomorrow. Not sure yet.",
        # Low compliance
        "No doctor, I cannot visit. Scared of dentist and treatment too painful.",
        "I will not come. I am busy. No time. Not interested.",
    ]

    for t in test_texts:
        result = model.analyze_conversation(t)
        print(f"\n{'='*70}")
        print(f"  Text    : {t}")
        print(f"  Found   : {', '.join(result['matched_keywords']) if result['matched_keywords'] else '(none)'}")
        print(f"  Counts  : High={result['high_count']}, Medium={result['medium_count']}, Low={result['low_count']}")
        print(f"  Score   : {result['compliance_percentage']}% [{result['compliance_level']}]")
        print(f"  Predict : {result['prediction']}")