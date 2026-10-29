(() => {
    const findCy = root => root && [...root.querySelectorAll("div")]
        .map(d => d._cyreg && d._cyreg.cy).find(Boolean);

    const zoomTo = (aioId, ids, zoomMax) => {
        if (!ids.length) return;
        const cy = findCy(document.querySelector(`[data-cytoscape-aio="${CSS.escape(aioId)}"]`));
        if (!cy) return;
        const eles = cy.collection();
        ids.forEach(id => eles.merge(cy.getElementById(id)));
        if (eles.empty()) return;
        const bb = eles.boundingBox(), w = cy.width(), h = cy.height(), pad = 50;
        let z = Math.min((w - 2 * pad) / bb.w, (h - 2 * pad) / bb.h, zoomMax);
        z = Math.max(cy.minZoom(), Math.min(cy.maxZoom(), z));
        cy.stop();
        cy.animate({
            zoom: z,
            pan: {x: (w - z * (bb.x1 + bb.x2)) / 2, y: (h - z * (bb.y1 + bb.y2)) / 2},
        }, {duration: 300});
    };

    const SELECTED = "#0169D9";
    const arrows = c => ({
        "source-arrow-color": c, "target-arrow-color": c,
        "mid-source-arrow-color": c, "mid-target-arrow-color": c,
    });
    // Cytoscape lets later rules win regardless of specificity, so :selected is restated
    // after the dark rules to keep cytoscape's default highlight.
    const DARK = [
        {selector: "node, edge", style: {color: "#C9C9C9"}},
        {selector: "node", style: {"background-color": "#828282"}},
        {selector: "edge", style: {"line-color": "#696969", ...arrows("#696969")}},
        {selector: ":selected", style: {
            "background-color": SELECTED, "line-color": SELECTED, ...arrows(SELECTED),
        }},
    ];
    const scheme = () => document.documentElement.getAttribute("data-mantine-color-scheme") === "dark"
        ? "dark" : "light";
    const themed = new Set();
    const setTheme = aioId => dash_clientside.set_props(
        {component: "CytoscapeAIO", subcomponent: "theme", aio_id: aioId}, {data: scheme()});
    new MutationObserver(() => themed.forEach(setTheme)).observe(document.documentElement, {attributeFilter: ["data-mantine-color-scheme"]});

    window.dash_clientside = window.dash_clientside || {};
    window.dash_clientside.cytoscape_aio = {
        sync(elements, value, selNodes, selEdges, labels, zoomVariant) {
            const NU = dash_clientside.no_update;
            const ctx = dash_clientside.callback_context;
            const zoom = ids => zoomVariant === "filled"
                && zoomTo(ctx.outputs_list[0].id.aio_id, ids, labels.zoomMax);
            const props = ctx.triggered
                .map(t => t.prop_id.slice(t.prop_id.lastIndexOf(".") + 1));
            const els = (elements || []).filter(e => {
                const ok = e.data && e.data.id != null;
                if (!ok) console.error("CytoscapeAIO: element without data.id", e);
                return ok;
            });
            const isEdge = e => e.group === "edges" || e.data.source !== undefined;
            const fill = (t, d) => t.replace(/\{(\w+)\}/g, (_, k) => d[k] ?? "");
            const item = (e, t) => ({value: String(e.data.id), label: fill(t, e.data)});
            const same = (a, b) => a.length === b.length && a.every(x => b.includes(x));
            const withSelection = ids => {
                let changed = false;
                const out = elements.map(e => {
                    if (!e.data || e.data.id == null) return e;
                    const want = ids.includes(String(e.data.id));
                    if (e.selected === want) return e;
                    changed = true;
                    return {...e, selected: want};
                });
                return changed ? out : NU;
            };

            const cur = value || [];
            let data = NU, newValue = NU, newElements = NU, nodeData = NU, edgeData = NU;

            if (props.includes("selectedNodeData") || props.includes("selectedEdgeData")) {
                const ids = [...(selNodes || []), ...(selEdges || [])].map(d => String(d.id));
                if (!same(ids, cur)) {
                    newValue = ids;
                    zoom(ids);
                }
                newElements = withSelection(ids);
            } else if (props.includes("value")) {
                newElements = withSelection(cur);
                if (newElements !== NU) zoom(cur);
            } else {
                data = [
                    {group: "Nodes", items: els.filter(e => !isEdge(e)).map(e => item(e, labels.node))},
                    {group: "Edges", items: els.filter(isEdge).map(e => item(e, labels.edge))},
                ];
                const known = new Set(els.map(e => String(e.data.id)));
                let ids = cur.filter(id => known.has(id));
                if (!props.includes("elements")) {
                    const picked = els.filter(e => e.selected);
                    ids = picked.map(e => String(e.data.id));
                    nodeData = picked.filter(e => !isEdge(e)).map(e => e.data);
                    edgeData = picked.filter(isEdge).map(e => e.data);
                }
                if (!same(ids, cur)) newValue = ids;
            }
            return [data, newValue, newElements, nodeData, edgeData];
        },

        toggleZoom(n, variant, value, cfg) {
            const on = variant !== "filled";
            if (on) {
                zoomTo(dash_clientside.callback_context.outputs_list[0].id.aio_id,
                    value || [], cfg.zoomMax);
            }
            return on ? ["filled", "tabler:zoom-in"] : ["default", "tabler:zoom-cancel"];
        },

        applyStyleOverride(overrides, theme, cfg) {
            const aioId = dash_clientside.callback_context.outputs_list.id.aio_id;
            themed.add(aioId);
            if (theme !== scheme()) setTheme(aioId);
            return (scheme() === "dark" ? DARK : []).concat(cfg.stylesheet,
                Object.entries(overrides || {}).map(([id, style]) =>
                    ({selector: `[id = ${JSON.stringify(id)}]${cfg.overrideSelected ? "" : ":unselected"}`, style})));
        },

        toggleTheme() {
            document.documentElement.setAttribute(
                "data-mantine-color-scheme", scheme() === "dark" ? "light" : "dark");
        },

        themeIcon(theme) {
            return theme === "dark" ? "tabler:sun" : "tabler:moon";
        },

                edgeText(cfg) {
            const aioId = dash_clientside.callback_context.inputs_list[0].id.aio_id;
            const cy = findCy(document.querySelector(`[data-cytoscape-aio="${CSS.escape(aioId)}"]`));
            if (!cy) return;
            const fill = (t, d) => t.replace(/\{(\w+)\}/g, (_, k) => d[k] ?? "");
            const write = edges => {
                const {parts, sep} = cy.scratch("_aioEdgeText");
                edges.forEach(e => {
                    // mirrors cytoscape's autorotate: text reads left to right, or top to bottom
                    const s = e.source().position(), t = e.target().position();
                    const dx = t.x - s.x, dy = t.y - s.y;
                    const texts = parts.map(p => fill(p, e.data())).filter(Boolean);
                    if (dx < 0 || (dx === 0 && dy < 0)) texts.reverse();
                    e.data("aio_edge_text", texts.join(sep));
                });
            };
            if (!cfg.edgeText) return;
            if (!cy.scratch("_aioEdgeText")) {
                cy.on("position", "node", ev => write(ev.target.connectedEdges()));
                cy.on("add", "edge", ev => write(ev.target));
            }
            cy.scratch("_aioEdgeText", {parts: cfg.edgeText, sep: cfg.edgeTextSep});
            write(cy.edges());
        },

        toggleInfo(n, variant) {
            return variant === "filled" ? "default" : "filled";
        },

        placeInfo(children, variant) {
            const aioId = dash_clientside.callback_context.inputs_list[0].id.aio_id;
            const sel = a => document.querySelector(`[${a}="${CSS.escape(aioId)}"]`);
            const root = sel("data-cytoscape-aio"), box = sel("data-cytoscape-aio-info");
            const cy = findCy(root);
            if (!cy || !box) return;
            const has = children != null && children !== ""
                && !(Array.isArray(children) && !children.length);
            if (!box._aio) {
                let raf = 0;
                const schedule = () => raf || (raf = requestAnimationFrame(() => {
                    raf = 0;
                    place();
                }));
                const place = () => {
                    const s = box._aio, picked = cy.$(":selected");
                    if (!s.on || !s.has || picked.empty()) {
                        box.style.display = "none";
                        return;
                    }
                    box.style.display = "block";
                    const c = cy.container().getBoundingClientRect();
                    const r = root.getBoundingClientRect();
                    const o = sel("data-cytoscape-aio-overlay").getBoundingClientRect();
                    const pw = box.offsetWidth, ph = box.offsetHeight;
                    const W = cy.width(), H = cy.height(), g = 12;
                    const b = picked.renderedBoundingBox();
                    const mx = (b.x1 + b.x2) / 2, my = (b.y1 + b.y2) / 2;
                    const cands = [
                        [b.x2 + g, my - ph / 2], [b.x1 - g - pw, my - ph / 2],
                        [mx - pw / 2, b.y2 + g], [mx - pw / 2, b.y1 - g - ph],
                    ];
                    const obstacles = cy.elements().map(e => e.renderedBoundingBox()).concat([{
                        x1: o.left - c.left, x2: o.right - c.left,
                        y1: o.top - c.top, y2: o.bottom - c.top,
                    }]);
                    const hits = ([x, y]) => obstacles.filter(q =>
                        q.x1 < x + pw && q.x2 > x && q.y1 < y + ph && q.y2 > y).length;
                    const clamp = (v, max) => Math.max(0, Math.min(v, max));
                    const [x, y] = cands
                        .filter(([x, y]) => x >= 0 && y >= 0 && x + pw <= W && y + ph <= H)
                        .reduce((best, p) => best && hits(best) <= hits(p) ? best : p, null)
                        || [clamp(cands[0][0], W - pw), clamp(cands[0][1], H - ph)];
                    box.style.left = `${x + c.left - r.left}px`;
                    box.style.top = `${y + c.top - r.top}px`;
                };
                box._aio = {schedule};
                cy.on("viewport position select unselect", schedule);
                new ResizeObserver(schedule).observe(box);
            }
            Object.assign(box._aio, {on: variant === "filled", has});
            box._aio.schedule();
        },
    };
})();
