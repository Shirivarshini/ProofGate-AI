# UI design system

React/Vite/JavaScript/JSX/Tailwind/React Router/Axios/Lucide React. Dark-first: canvas `#0B1020`, surface `#121A2E`, raised `#1B2642`, text `#E8EDF8`, muted `#9BA8C3`, accent `#68A7FF`; approve `#2DD4A8`, block `#FB7185`, review `#FBBF24`, low/medium/high `#38BDF8/#FBBF24/#F97316`. Use Inter/system 14px body, 20px section, 28px page title; 4/8/12/16/24/32 spacing; 8px cards, 12px dialogs; 256px desktop sidebar.

Pages: Overview Dashboard (metrics and recent actions), Agent Playground (clearly labeled simulated request/proposal), Human Reviews (evidence and decision dialog), Audit Logs (filterable timeline/table). Components: Sidebar, Header, Metric Card, Action Card, Status Badge, Risk Indicator, Evidence Panel, Verification Timeline, Review Decision Dialog, Audit Table, Empty/Error/Loading State.

Use labelsâ€”not color aloneâ€”plus icons, focus rings, keyboard dialog control, WCAG AA contrast, responsive breakpoints 640/768/1024px, skeleton loading and retryable errors. `APPROVE` and `EXECUTED` must always appear as different badges. Mock data requires a visible â€œMock dataâ€ label. Browser never holds gateway authorization or calls protected tools.

