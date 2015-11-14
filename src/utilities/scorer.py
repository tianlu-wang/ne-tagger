def evaluate_tagging(eval_tab_path, selected_il):
    def process_tab_file(eval_file_path, doc_ids):
        tab_file = io.open(eval_file_path, 'r', -1, 'utf-8')

        tab_file_dict = {}
        for line in tab_file:
            line = line.strip().split('\t')
            offset = line[3]
            doc_id = offset.split(':')[0]
            if doc_id not in doc_ids:
                continue
            type = line[5]
            tab_file_dict[offset] = type

        return tab_file_dict

    def get_doc_ids(eval_file_path):
        doc_ids = set()
        tab_file = io.open(eval_file_path, 'r', -1, 'utf-8')
        for line in tab_file:
            doc_id = line.strip().split('\t')[3].split(':')[0]
            doc_ids.add(doc_id)
        return doc_ids

    def safe_divide(a, b):
        if b == 0:
            return 0
        return round(a / float(b), 2)

    # run scorer
    if selected_il == 'hausa':
        ground_truth_path = os.path.join(APP_ROOT, 'eval/gold/hau_all_gold_without_ttl_and_sn.tab')
    elif selected_il == 'yoruba':
        ground_truth_path = os.path.join(APP_ROOT, 'eval/gold/yoruba_all_gold_without_ttl.tab')
    elif selected_il == 'turkish':
        ground_truth_path = os.path.join(APP_ROOT, 'eval/gold/turkish_all_gold_without_ttl.tab')

    # preproccessing eval-tab file
    doc_ids = get_doc_ids(eval_tab_path)
    eval_tab = process_tab_file(eval_tab_path, doc_ids)
    gold_tab = process_tab_file(ground_truth_path, doc_ids)

    # mention identification performance
    correctly_identified_mentions = 0
    correctly_per_id = 0
    correctly_org_id = 0
    correctly_gpe_id = 0

    # system mention types
    system_per = 0
    system_org = 0
    system_gpe = 0

    for key in eval_tab:
        if eval_tab[key] == 'PER':
            system_per += 1
        if eval_tab[key] == 'ORG':
            system_org += 1
        if eval_tab[key] == 'LOC' or eval_tab[key] == 'GPE':
            system_gpe += 1

        if key in gold_tab.keys():
            correctly_identified_mentions += 1
            if eval_tab[key] == 'PER':
                correctly_per_id += 1
            if eval_tab[key] == 'ORG':
                correctly_org_id += 1
            if eval_tab[key] == 'LOC' or eval_tab[key] == 'GPE':
                correctly_gpe_id += 1

    gold_id_per = 0
    gold_id_org = 0
    gold_id_gpe = 0

    for value in gold_tab.values():
        if value == 'PER':
            gold_id_per += 1
        if value == 'ORG':
            gold_id_org += 1
        if value == 'LOC' or value == 'GPE':
            gold_id_gpe += 1

    total_identified_mentions = len(eval_tab)
    gold_identified_mentions = len(gold_tab)

    per_id_prec = safe_divide(correctly_per_id, system_per)
    per_id_recall = safe_divide(correctly_per_id, gold_id_per)
    per_id_f1 = safe_divide(2.0*per_id_prec*per_id_recall, per_id_prec+per_id_recall)

    org_id_prec = safe_divide(correctly_org_id, system_org)
    org_id_recall = safe_divide(correctly_org_id, gold_id_org)
    org_id_f1 = safe_divide(2.0*org_id_prec*org_id_recall, org_id_prec+org_id_recall)

    gpe_id_prec = safe_divide(correctly_gpe_id, system_gpe)
    gpe_id_recall = safe_divide(correctly_gpe_id, gold_id_gpe)
    gpe_id_f1 = safe_divide(2.0*gpe_id_prec*gpe_id_recall, gpe_id_prec+gpe_id_recall)

    identification_prec = safe_divide(correctly_identified_mentions, total_identified_mentions)
    identification_recall = safe_divide(correctly_identified_mentions, gold_identified_mentions)
    identification_f1 = safe_divide(2.0*identification_prec*identification_recall,
                                    identification_prec+identification_recall)

    # mention classification performance
    # it evaluates the classification performance of perfectly identified mentions
    gold_per = 0
    gold_org = 0
    gold_gpe = 0

    # system perfect mention types
    perf_system_per = 0
    perf_system_org = 0
    perf_system_gpe = 0

    correctly_classified_per = 0
    correctly_classified_org = 0
    correctly_classified_gpe = 0

    for key in eval_tab:
        if key in gold_tab.keys():
            if eval_tab[key] == 'PER':
                perf_system_per += 1
            elif eval_tab[key] == 'ORG':
                perf_system_org += 1
            elif eval_tab[key] in ['GPE', 'LOC']:
                perf_system_gpe += 1

            if gold_tab[key] == 'PER':
                gold_per += 1
            elif gold_tab[key] == 'ORG':
                gold_org += 1
            elif gold_tab[key] in ['GPE', 'LOC']:
                gold_gpe += 1

            if eval_tab[key].replace('GPE', 'LOC') == gold_tab[key]:
                if eval_tab[key] == 'PER':
                    correctly_classified_per += 1
                elif eval_tab[key] == 'ORG':
                    correctly_classified_org += 1
                elif eval_tab[key] in ['GPE', 'LOC']:
                    correctly_classified_gpe += 1

    per_prec = safe_divide(correctly_classified_per, perf_system_per)
    per_recall = safe_divide(correctly_classified_per, gold_per)
    per_f1 = safe_divide(2.0*per_prec*per_recall, per_prec+per_recall)

    org_prec = safe_divide(correctly_classified_org, perf_system_org)
    org_recall = safe_divide(correctly_classified_org, gold_org)
    org_f1 = safe_divide(2.0*org_prec*org_recall, org_prec+org_recall)

    gpe_prec = safe_divide(correctly_classified_gpe, perf_system_gpe)
    gpe_recall = safe_divide(correctly_classified_gpe, gold_gpe)
    gpe_f1 = safe_divide(2.0*gpe_prec*gpe_recall, gpe_prec+gpe_recall)

    correctly_classified_total = correctly_classified_per + correctly_classified_org + correctly_classified_gpe
    perf_system_total = perf_system_per + perf_system_org + perf_system_gpe
    gold_total = gold_per + gold_org + gold_gpe

    classification_prec = safe_divide(correctly_classified_total, perf_system_total)
    classification_recall = safe_divide(correctly_classified_total, gold_total)
    classification_f1 = safe_divide(2.0*classification_prec*classification_recall,
                                    classification_prec+classification_recall)

    # end to end system performance
    e2e_prec = safe_divide(correctly_classified_total, total_identified_mentions)
    e2e_recall = safe_divide(correctly_classified_total, gold_identified_mentions)
    e2e_f1 = safe_divide(2.0*e2e_prec*e2e_recall, e2e_prec+e2e_recall)

    result = {
        'identification_prec': identification_prec,
        'identification_recall': identification_recall,
        'identification_f1':  identification_f1,
        'per_id_prec': per_id_prec,
        'per_id_recall': per_id_recall,
        'per_id_f1': per_id_f1,
        'org_id_prec': org_id_prec,
        'org_id_recall': org_id_recall,
        'org_id_f1': org_id_f1,
        'gpe_id_prec': gpe_id_prec,
        'gpe_id_recall': gpe_id_recall,
        'gpe_id_f1': gpe_id_f1,
        'per_prec': per_prec,
        'per_recall': per_recall,
        'per_f1': per_f1,
        'org_prec': org_prec,
        'org_recall': org_recall,
        'org_f1': org_f1,
        'gpe_prec': gpe_prec,
        'gpe_recall': gpe_recall,
        'gpe_f1': gpe_f1,
        'typing_prec': classification_prec,
        'typing_recall': classification_recall,
        'typing_f1': classification_f1,
        'e2e_prec': e2e_prec,
        'e2e_recall': e2e_recall,
        'e2e_f1': e2e_f1,
        'evaluated_doc_num': len(doc_ids)
    }

    return result