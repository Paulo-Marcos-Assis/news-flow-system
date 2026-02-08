# extractors/utils/unit_substitutions.py

# extractors/utils/unit_substitutions.py

SUBSTITUICOES = {
    # ATUALIZADO: Adicionado 'am[s]?'
    r'\b(ap|am[s]?|amp|ampo|ampola[s]?)\b': 'ampola',
    r'\b(bd|balde[s]?)\b': 'balde',
    r'\b(bandeja[s]?)\b': 'bandeja',
    r'\b(br|barra[s]?)\b': 'barra',
    # ATUALIZADO: Adicionado 'bisn'
    r'\b(bg|bn|bng[s]?|bis|bisn|bisnaga[s]?|bs)\b': 'bisnaga',
    r'\b(bl[s]?|bt[s]?|blis(t)?[s]?|blister[s]?)\b': 'blister',
    r'\b(bloco[s]?)\b': 'bloco',
    # NOVO: Adicionado 'bolsa'
    r'\b(bol[s]?|bolsa[s]?|blsa[s]?)\b': 'bolsa',
    r'\b(bobina[s]?)\b': 'bobina',
    r'\b(bombona[s]?)\b': 'bombona',
    # ATUALIZADO: Adicionado 'cap[s]?' (para cobrir caps)
    r'\b(cap[s]?|capsula[s]?)\b': 'capsula',
    r'\b(cartela[s]?)\b': 'cartela',
    r'\b(cj|conjunto[s]?)\b': 'conjunto',
    r'\b(centimetro[s]?|cm\b)\b': 'cm',
    r'\b(cm[\s]?2|cm²|centimetro[s]?[\s]?2)\b': 'cm2',
    # ATUALIZADO: Adicionado 'cxs' e 'cda'
    r'\b(?:caix[a]?|cax[a]?|cxa|cx|cxs|cda)(\d*)\b': 'caixa',
    r'\b(ct|cento[s]?|ct[s]?)\b': 'cento',
    # ATUALIZADO: Adicionado 'cpd[s]?'
    r'\b(com(p(ri)?)?[s]?|cp[s]?|cpr[s]?|cmp[s]?|cpd[s]?|comprimido[s]?)\b': 'comprimido',
    r'\b(display[s]?|disp[s]?)\b': 'display',
    # NOVO: Adicionado 'dragea'
    r'\b(drg[s]?|dragea[s]?|dra)\b': 'dragea',
    r'\b(duzia[s]?|dz[s]?)\b': 'duzia',
    r'\b(embalagem[s]?|emb[s]?)\b': 'embalagem',
    # NOVO: Adicionado 'envelope'
    r'\b(ev|env[s]?|envelope[s]?)\b': 'envelope',
    r'\b(fd|fardo[s]?|fd[s]?)\b': 'fardo',
    r'\b(folha[s]?|fl[s]?)\b': 'folha',
    # ATUALIZADO: Adicionado 'fra[s]?'
    r'\b(frasco[s]?|fr[s]?|fra[s]?|frc)\b': 'frasco',
    r'\b(fa[s]?|famp[s]?|frasampo[s]?|frascoampola[s]?|frasco[\s]?amp(ola)?[s]?)\b': 'frasco-ampola',
    r'\b(gl|gl[s]?|gal(ao|oes|s)?)\b': 'galao',
    r'\b(garrafa[s]?|garf[s]?|garf?)\b': 'garrafa',
    r'\b(g|grama[s]?|gr[s]?|g\b)\b': 'gramas',
    r'\b(jg|jgo|jog|jogo?s?)\b': 'jogo',
    r'\b(quilate[s]?|kt[s]?|ct[s]?)\b': 'quilate',
    r'\b(kg1|kg[s]?|kilo[s]?|quilo[s]?|kilograma[s]?|quilograma[s]?)\b': 'kilograma',
    r'\b(kit[s]?|kts|ki)\b': 'kit',
    r'\b(lata[s]?)\b': 'lata',
    r'\b(litro[s]?|lit[s]?|ltr[s]?|lt[s]?|l\b)\b': 'litro',
    r'\b(m[\s]?2|m²)\b': 'metro2',
    r'\b(m[\s]?3|m³)\b': 'metro3',
    r'\b(metro[s]?|metr[o]?|mt[s]?|m)\b': 'metro',
    r'\b(mili|mililitro[s]?|ml[s]?)\b': 'mililitro',
    r'\b(mi|milheiro[s]?)\b': 'milheiro',
    r'\b(mwh[s]?)\b': 'mwh',
    r'\b(pacote[s]?|pct[s]?|pcts?|pacte[s]?)\b': 'pacote',
    r'\b(palete[s]?|palet[s]?|pallet[s]?)\b': 'palete',
    r'\b(pr|par(es)?|pr[s]?)\b': 'par',
    # ATUALIZADO: Adicionado 'pce[s]?' e 'peça[s]?'
    r'\b(pca|pc[s]?|peca[s]?|pec[s]?|pce[s]?|peça[s]?)\b': 'peca',
    r'\b(pt|pote[s]?)\b': 'pote',
    r'\b(resma[s]?)\b': 'resma',
    r'\b(rolo[s]?|rl[s]?)\b': 'rolo',
    # NOVO: Adicionado 'sache'
    r'\b(sch[s]?|sache[s]?|sachê[s]?)\b': 'sache',
    r'\b(saco[s]?|sc[s]?|scos?)\b': 'saco',
    r'\b(sacola[s]?|sac[s]?)\b': 'sacola',
    r'\b(tambor[es]?|tbr[s]?)\b': 'tambor',
    r'\b(to|tonelada[s]?|ton[s]?|t|tn|tns)\b': 'tonelada',
    # ATUALIZADO: Adicionado 'tbo[s]?'
    r'\b(tubo[s]?|tb[s]?|tbo[s]?|tub)\b': 'tubo',
    # ATUALIZADO: Adicionado 'ud\d*'
    r'\b(u|ud\d*|und(?:\.?)\d*|unid(?:ade)?s?\d*|unidad\d*|un\d*\b|uni\d*\b|unit\b|unt\b)\b': 'unidade',
    r'\b(vidro[s]?|vd[s]?)\b': 'vidro',
}
