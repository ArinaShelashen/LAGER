// ruleview.js – reads MØD rules in GML format and draws them as three panels
// (L = left side, K = what stays, R = right side), in the style of MolFoundry:
// atoms as dashed circles, bonds that are removed in red (L),
// bonds that are formed in green (R), both drawn thicker. Click an atom to highlight it in all panels.
//
// Usage:  const rule = RuleView.parse(gmlText);   // throws on syntax errors
//         RuleView.render(containerElement, rule);

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // 1. GML text -> nested lists of [key, value]
  // -------------------------------------------------------------------------
  function tokenize(text) {
    const tokens = [];
    let i = 0;
    while (i < text.length) {
      const c = text[i];
      if (/\s/.test(c)) { i++; continue; }
      if (c === "#") {                                   // comment until end of line
        while (i < text.length && text[i] !== "\n") i++;
        continue;
      }
      if (c === "[" || c === "]") { tokens.push({ type: c }); i++; continue; }
      if (c === '"') {
        let j = i + 1, value = "";
        while (j < text.length && text[j] !== '"') {
          if (text[j] === "\\" && j + 1 < text.length) { value += text[j + 1]; j += 2; }
          else value += text[j++];
        }
        if (j >= text.length) throw new Error("A text in quotes (\"…\") is not closed.");
        tokens.push({ type: "string", value });
        i = j + 1;
        continue;
      }
      let j = i;
      while (j < text.length && !/[\s\[\]"]/.test(text[j])) j++;
      const word = text.slice(i, j);
      tokens.push(/^-?\d+(\.\d+)?$/.test(word) ? { type: "number", value: Number(word) }
                                                : { type: "word", value: word });
      i = j;
    }
    return tokens;
  }

  function parseList(tokens, pos, topLevel) {
    const items = [];
    while (pos.i < tokens.length) {
      const t = tokens[pos.i];
      if (t.type === "]") {
        if (topLevel) throw new Error("There is a ']' without a matching '['.");
        pos.i++;
        return items;
      }
      if (t.type !== "word") throw new Error(`Expected a key, found "${t.value ?? t.type}".`);
      pos.i++;
      const v = tokens[pos.i];
      if (!v) throw new Error(`The key "${t.value}" has no value.`);
      pos.i++;
      if (v.type === "[") items.push([t.value, parseList(tokens, pos, false)]);
      else if (v.type === "string" || v.type === "number") items.push([t.value, v.value]);
      else throw new Error(`The key "${t.value}" has an invalid value.`);
    }
    if (!topLevel) throw new Error("A '[' is not closed with ']'.");
    return items;
  }

  const get = (list, key) => (list.find(([k]) => k === key) || [])[1];
  const getAll = (list, key) => list.filter(([k]) => k === key).map(([, v]) => v);
  const labelsOf = (list) => (Array.isArray(list) ? getAll(list, "label").map(String) : []);

  // -------------------------------------------------------------------------
  // 2. Lists -> rule model
  // -------------------------------------------------------------------------
  function parse(text) {
    const top = parseList(tokenize(text), { i: 0 }, true);
    const body = get(top, "rule");
    if (!Array.isArray(body)) throw new Error('The text must contain "rule [ … ]".');

    const nodes = new Map();      // id -> {id, left, context, right}  (labels per part)
    const edges = new Map();      // "a-b" -> {a, b, left, context, right}
    const warnings = [];

    for (const part of ["left", "context", "right"]) {
      const section = get(body, part);
      if (section === undefined) continue;
      if (!Array.isArray(section)) throw new Error(`"${part}" must be a list [ … ].`);
      for (const n of getAll(section, "node")) {
        const id = get(n, "id"), label = get(n, "label");
        if (id === undefined) throw new Error(`A node in "${part}" has no id.`);
        if (!nodes.has(id)) nodes.set(id, { id });
        const node = nodes.get(id);
        if (node[part] !== undefined) warnings.push(`Node ${id} appears twice in "${part}".`);
        node[part] = label === undefined ? "" : String(label);
      }
      for (const e of getAll(section, "edge")) {
        const s = get(e, "source"), t = get(e, "target"), label = get(e, "label");
        if (s === undefined || t === undefined) throw new Error(`An edge in "${part}" has no source or target.`);
        const [a, b] = s < t ? [s, t] : [t, s];
        const key = `${a}-${b}`;
        if (!edges.has(key)) edges.set(key, { a, b });
        edges.get(key)[part] = label === undefined ? "" : String(label);
      }
    }
    if (!nodes.size) throw new Error("The rule has no atoms (nodes).");

    // Which side each atom belongs to
    for (const n of nodes.values()) {
      n.inL = n.context !== undefined || n.left !== undefined;
      n.inR = n.context !== undefined || n.right !== undefined;
      n.inK = n.context !== undefined || (n.left !== undefined && n.right !== undefined);
      n.labelL = n.context ?? n.left;
      n.labelR = n.context ?? n.right;
      n.changed = n.context === undefined && n.left !== undefined && n.right !== undefined
                  && n.left !== n.right;
    }
    for (const e of edges.values()) {
      for (const side of ["L", "R"]) {
        const part = side === "L" ? "left" : "right";
        const present = e.context !== undefined || e[part] !== undefined;
        if (present && !(nodes.get(e.a)?.[`in${side}`] && nodes.get(e.b)?.[`in${side}`])) {
          warnings.push(`Bond ${e.a}–${e.b} connects an atom that is missing on the ${part} side.`);
        }
      }
    }

    // Constraints
    const constraints = [];
    for (const [key, value] of body) {
      if (!key.startsWith("constrain")) continue;
      constraints.push({ type: key, raw: value });
    }

    return {
      id: get(body, "ruleID") ?? "",
      labelType: get(body, "labelType") ?? "string",
      nodes, edges, constraints, warnings,
    };
  }

  // -------------------------------------------------------------------------
  // 3. Constraints in words
  // -------------------------------------------------------------------------
  const OPS = { "=": "exactly", "<": "fewer than", "<=": "at most", ">": "more than", ">=": "at least" };

  function describeConstraint(c) {
    const v = c.raw;
    if (c.type === "constrainAdj" && Array.isArray(v)) {
      const id = get(v, "id"), op = get(v, "op") ?? "=", count = get(v, "count");
      const nodeLabels = labelsOf(get(v, "nodeLabels"));
      const edgeLabels = labelsOf(get(v, "edgeLabels"));
      let text = `Atom ${id} must have ${OPS[op] || op} ${count} neighbour${count === 1 ? "" : "s"}`;
      if (nodeLabels.length) text += ` labelled ${nodeLabels.join(" or ")}`;
      if (edgeLabels.length) text += ` bonded by ${edgeLabels.map(bondName).join(" or ")}`;
      return { text, nodeIds: id === undefined ? [] : [id] };
    }
    if (c.type === "constrainLabelAny" && Array.isArray(v)) {
      return { text: `Label ${get(v, "label")} can be ${labelsOf(get(v, "labels")).join(", ")}`, nodeIds: [] };
    }
    if (c.type === "constrainShortestPath" && Array.isArray(v)) {
      const op = get(v, "op") ?? "=";
      return {
        text: `The shortest path between atoms ${get(v, "source")} and ${get(v, "target")} must be ` +
              `${OPS[op] || op} ${get(v, "length")} bonds long`,
        nodeIds: [get(v, "source"), get(v, "target")],
      };
    }
    return { text: `${c.type}: ${JSON.stringify(v)}`, nodeIds: [] };
  }

  function bondName(label) {
    return { "-": "single bond (-)", "=": "double bond (=)", "#": "triple bond (#)",
             ":": "aromatic bond (:)" }[label] || `"${label}"`;
  }

  // -------------------------------------------------------------------------
  // 4. Layout: one set of positions for all three panels (force-directed)
  // -------------------------------------------------------------------------
  function layout(rule) {
    const ids = [...rule.nodes.keys()].sort((a, b) => a - b);
    const index = new Map(ids.map((id, i) => [id, i]));
    const n = ids.length;
    const pos = ids.map((_, i) => {                     // deterministic start: a circle
      const angle = (2 * Math.PI * i) / n;
      return { x: Math.cos(angle) * 40 * Math.sqrt(n), y: Math.sin(angle) * 40 * Math.sqrt(n) };
    });
    const links = [...rule.edges.values()].map((e) => [index.get(e.a), index.get(e.b)]);
    const L = 52;                                       // preferred bond length
    let temperature = 40;
    for (let step = 0; step < 600; step++) {
      const force = pos.map(() => ({ x: 0, y: 0 }));
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          let dx = pos[i].x - pos[j].x, dy = pos[i].y - pos[j].y;
          let d = Math.hypot(dx, dy);
          if (d < 0.01) { dx = 0.01 * (i - j); dy = 0.01; d = Math.hypot(dx, dy); }
          if (d > 3.5 * L) continue;                      // far-away atoms don't push
          const f = (L * L) / d;
          force[i].x += (dx / d) * f; force[i].y += (dy / d) * f;
          force[j].x -= (dx / d) * f; force[j].y -= (dy / d) * f;
        }
      }
      for (const [i, j] of links) {
        const dx = pos[i].x - pos[j].x, dy = pos[i].y - pos[j].y;
        const d = Math.max(Math.hypot(dx, dy), 0.01);
        const f = (d * d) / L;
        force[i].x -= (dx / d) * f; force[i].y -= (dy / d) * f;
        force[j].x += (dx / d) * f; force[j].y += (dy / d) * f;
      }
      for (let i = 0; i < n; i++) {
        force[i].x -= pos[i].x * 0.08;                  // weak pull to the centre keeps
        force[i].y -= pos[i].y * 0.08;                  // separate fragments together
        const f = Math.hypot(force[i].x, force[i].y);
        if (f > 0) {
          const move = Math.min(f, temperature);
          pos[i].x += (force[i].x / f) * move;
          pos[i].y += (force[i].y / f) * move;
        }
      }
      temperature = Math.max(0.5, temperature * 0.985);
    }
    return new Map(ids.map((id, i) => [id, pos[i]]));
  }

  // -------------------------------------------------------------------------
  // 5. Drawing
  // -------------------------------------------------------------------------
  const SVG = "http://www.w3.org/2000/svg";
  const R_ATOM = 17;
  const COLORS = { bond: "#3c4043", removed: "#d93025", added: "#0f9d58", selected: "#f9ab00",
                   atomFill: "#ffffff", atomStroke: "#3c4043", text: "#202124", id: "#80868b" };

  // Usual element colours (CPK/Jmol), darkened where needed to be readable on white
  const ELEMENT_COLORS = {
    H: "#6b6b6b", C: "#202124", N: "#2346d9", O: "#d32f2f", F: "#2e8b2e", Cl: "#1f9a1f",
    Br: "#a52a2a", I: "#8e24aa", S: "#b58900", P: "#e07000", B: "#d0706f", Si: "#a07850",
    Li: "#8e44ad", Na: "#7b3fc4", K: "#6a32b0", Mg: "#2e7d32", Ca: "#2e7d32", Zn: "#5c6bc0",
    Cu: "#b8692e", Fe: "#c0582b", Pd: "#00697f", Pt: "#6f7f8f", Sn: "#5f7f7f", Se: "#c77800",
  };

  function svgEl(tag, attrs, parent) {
    const e = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (parent) parent.appendChild(e);
    return e;
  }

  // "Cl-" -> Cl with superscript minus, "2H" -> H with superscript 2
  function drawLabel(parent, label, x, y, small) {
    const t = svgEl("text", { x, y: y + (small ? 4 : 5), "text-anchor": "middle", fill: COLORS.text,
                             "font-size": small ? 10 : 14, "font-family": "Georgia, 'Times New Roman', serif" },
                    parent);
    const m = /^(\d*)([A-Za-z_][A-Za-z0-9_]*?)(\d*[+-]+)?$/.exec(label);
    if (!m) { t.textContent = label; return; }
    const [, isotope, symbol, charge] = m;
    t.setAttribute("fill", ELEMENT_COLORS[symbol] || COLORS.text);   // wildcards (_X) stay dark grey
    if (isotope) svgEl("tspan", { "font-size": "0.65em", dy: "-0.5em" }, t).textContent = isotope;
    svgEl("tspan", isotope ? { dy: "0.5em" } : {}, t).textContent = symbol;
    if (charge) {
      svgEl("tspan", { "font-size": "0.65em", dy: "-0.6em" }, t)
        .textContent = charge.replace(/-/g, "\u2212");
    }
  }

  function drawBond(g, p, q, label, color) {
    const dx = q.x - p.x, dy = q.y - p.y, d = Math.hypot(dx, dy) || 1;
    const ux = dx / d, uy = dy / d, nx = -uy, ny = ux;
    const a = { x: p.x + ux * R_ATOM, y: p.y + uy * R_ATOM };
    const b = { x: q.x - ux * R_ATOM, y: q.y - uy * R_ATOM };
    const width = color === COLORS.bond ? 2 : 3.5;          // broken / formed bonds are thicker
    const line = (off, dashed) => svgEl("line", {
      x1: a.x + nx * off, y1: a.y + ny * off, x2: b.x + nx * off, y2: b.y + ny * off,
      stroke: color, "stroke-width": width, "stroke-linecap": "round",
      ...(dashed ? { "stroke-dasharray": "4 3" } : {}),
    }, g);
    const gap = width > 2 ? 1.3 : 1;                         // keep thick double bonds apart
    if (label === "=") { line(-3 * gap, false); line(3 * gap, false); }
    else if (label === "#") { line(-4.5 * gap, false); line(0, false); line(4.5 * gap, false); }
    else if (label === ":") { line(-2.5, false); line(2.5, true); }
    else {
      line(0, false);
      if (label !== "-" && label !== "") {               // wildcard or unusual bond label
        const mx = (a.x + b.x) / 2 + nx * 9, my = (a.y + b.y) / 2 + ny * 9;
        svgEl("text", { x: mx, y: my + 3, fill: color, "font-size": 10, "text-anchor": "middle",
                        "font-family": "sans-serif" }, g).textContent = label;
      }
    }
  }

  function drawPanel(container, rule, positions, side, box, state) {
    const panel = document.createElement("div");
    panel.className = "rv-panel";
    const title = document.createElement("span");
    title.className = "rv-panel-title";
    title.textContent = side;
    panel.appendChild(title);
    const svg = svgEl("svg", { viewBox: box.join(" "), preserveAspectRatio: "xMidYMid meet" });
    panel.appendChild(svg);
    container.appendChild(panel);

    const bonds = svgEl("g", {}, svg);
    for (const e of rule.edges.values()) {
      let label, color;
      if (side === "K") {
        if (e.context === undefined) continue;
        label = e.context; color = COLORS.bond;
      } else {
        const part = side === "L" ? "left" : "right";
        if (e.context !== undefined) { label = e.context; color = COLORS.bond; }
        else if (e[part] !== undefined) { label = e[part]; color = side === "L" ? COLORS.removed : COLORS.added; }
        else continue;
      }
      const p = positions.get(e.a), q = positions.get(e.b);
      if (p && q) drawBond(bonds, p, q, label, color);
    }

    const atoms = svgEl("g", {}, svg);
    for (const node of rule.nodes.values()) {
      if (!node[`in${side}`]) continue;
      const { x, y } = positions.get(node.id);
      const g = svgEl("g", { class: "rv-atom", "data-id": node.id }, atoms);
      const onlyHere = node.context === undefined && !node.inK;      // atom created or deleted
      const accent = side === "L" ? COLORS.removed : COLORS.added;
      svgEl("circle", {
        cx: x, cy: y, r: R_ATOM, fill: COLORS.atomFill,
        stroke: (node.changed || onlyHere) && side !== "K" ? accent : COLORS.atomStroke,
        "stroke-width": 2, "stroke-dasharray": node.changed || onlyHere ? "none" : "4 3",
      }, g);
      if (state.highlighted.has(node.id)) {
        svgEl("circle", { cx: x, cy: y, r: R_ATOM + 3, fill: "none",
                          stroke: COLORS.selected, "stroke-width": 4 }, g);
      }
      if (side === "K" && node.changed) {
        drawLabel(g, node.left, x, y - 6, true);         // label changes: L above, R below
        drawLabel(g, node.right, x, y + 6, true);
      } else {
        drawLabel(g, side === "R" ? node.labelR : side === "L" ? node.labelL : node.context ?? node.left, x, y, false);
      }
      svgEl("text", { x: x + R_ATOM + 1, y: y - R_ATOM + 4, fill: COLORS.id, "font-size": 9,
                      "font-family": "sans-serif" }, g).textContent = node.id;
      g.addEventListener("click", () => state.select(node.id));
    }
  }

  function atomInfo(rule, id) {
    const n = rule.nodes.get(id);
    if (!n) return "";
    if (n.context !== undefined) return `Atom ${id}: ${n.context} (unchanged, in L, K and R)`;
    if (n.changed) return `Atom ${id}: label changes from ${n.left} to ${n.right}`;
    if (n.left !== undefined && n.right !== undefined) return `Atom ${id}: ${n.left}`;
    if (n.left !== undefined) return `Atom ${id}: ${n.left} (removed: only in L)`;
    return `Atom ${id}: ${n.right} (created: only in R)`;
  }

  function render(container, rule) {
    const positions = layout(rule);
    const xs = [...positions.values()].map((p) => p.x), ys = [...positions.values()].map((p) => p.y);
    const pad = R_ATOM + 22;
    const minX = Math.min(...xs) - pad, minY = Math.min(...ys) - pad;
    const w = Math.max(Math.max(...xs) - Math.min(...xs) + 2 * pad, 240);
    const h = Math.max(Math.max(...ys) - Math.min(...ys) + 2 * pad, 190);
    const box = [minX - (w - (Math.max(...xs) - Math.min(...xs) + 2 * pad)) / 2,
                 minY - (h - (Math.max(...ys) - Math.min(...ys) + 2 * pad)) / 2, w, h];

    const described = rule.constraints.map(describeConstraint);
    const state = {
      highlighted: new Set(),
      select(id) {
        state.highlighted = state.highlighted.size === 1 && state.highlighted.has(id) ? new Set() : new Set([id]);
        draw();
        info.textContent = state.highlighted.size ? atomInfo(rule, id) : "Click an atom to highlight it in all three panels.";
      },
    };

    container.innerHTML = "";
    const root = document.createElement("div");        // wrapper, so clearing the container
    root.className = "rv";                              // removes the dark box too
    container.appendChild(root);
    container = root;
    const panels = document.createElement("div");
    panels.className = "rv-panels";
    container.appendChild(panels);
    const info = document.createElement("p");
    info.className = "rv-info";
    info.textContent = "Click an atom to highlight it in all three panels.";
    container.appendChild(info);

    const legend = document.createElement("p");
    legend.className = "rv-legend";
    legend.innerHTML =
      '<span class="rv-key rv-key-removed"></span> bond removed (only in L) ' +
      '<span class="rv-key rv-key-added"></span> bond formed (only in R) ' +
      '<span class="rv-key rv-key-kept"></span> unchanged';
    container.appendChild(legend);

    if (described.length) {
      const heading = document.createElement("p");
      heading.className = "rv-subtitle";
      heading.textContent = "Conditions";
      container.appendChild(heading);
      const list = document.createElement("ul");
      list.className = "rv-constraints";
      for (const d of described) {
        const li = document.createElement("li");
        li.textContent = d.text;
        if (d.nodeIds.length) {
          li.addEventListener("mouseenter", () => { state.highlighted = new Set(d.nodeIds); draw(); });
          li.addEventListener("mouseleave", () => { state.highlighted = new Set(); draw(); });
        }
        list.appendChild(li);
      }
      container.appendChild(list);
    }
    if (rule.warnings.length) {
      const warn = document.createElement("ul");
      warn.className = "rv-warnings";
      for (const w of rule.warnings) {
        const li = document.createElement("li");
        li.textContent = w;
        warn.appendChild(li);
      }
      container.appendChild(warn);
    }

    function draw() {
      panels.innerHTML = "";
      for (const side of ["L", "K", "R"]) drawPanel(panels, rule, positions, side, box, state);
    }
    draw();
  }

  window.RuleView = { parse, render, describeConstraint };
})();
