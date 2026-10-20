import { SiteHeader } from "@/components/site-header";

const approach = [
  {
    title: "Dados com contexto",
    description: "Qualidade, origem e população fazem parte da análise. Cada resultado precisa de uma base que possa ser conferida.",
    detail: "Ingestão e exploração",
  },
  {
    title: "Modelos com referência",
    description: "Pipelines de aprendizado e comparação com baseline ajudam a avaliar as escolhas, mantendo o teste final reservado.",
    detail: "Modelagem e avaliação",
  },
  {
    title: "Políticas com hipóteses",
    description: "A simulação compara limiares de aprovação com premissas explícitas de exposição, perda e receita.",
    detail: "Simulação de cenários",
  },
];

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main id="conteudo" tabIndex={-1}>
        <section id="projeto" aria-labelledby="project-title" className="scroll-mt-6 border-b border-line">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 py-16 sm:px-10 sm:py-24 lg:grid-cols-[1.45fr_1fr] lg:items-center lg:gap-20 lg:px-14">
            <div>
              <p className="mb-6 text-xs font-bold uppercase tracking-[0.18em] text-teal">Análise de risco de crédito</p>
              <h1 id="project-title" className="max-w-3xl text-4xl font-semibold leading-[1.12] tracking-tight text-navy sm:text-5xl lg:text-6xl">
                Decisões de crédito começam com boas perguntas.
              </h1>
              <p className="mt-7 max-w-xl text-lg leading-relaxed text-muted">
                Como equilibrar aprovação e risco de inadimplência? O Credit Risk Intelligence explora esse problema por meio de dados, modelos e simulação de políticas.
              </p>
              <a href="#abordagem" className="mt-9 inline-flex min-h-12 items-center gap-5 rounded-lg bg-navy px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-navy-light">
                Conhecer a abordagem <span aria-hidden="true">↗</span>
              </a>
              <p className="mt-5 text-xs leading-relaxed text-muted">Projeto educacional · Engenharia analítica · Portfólio</p>
            </div>
            <aside aria-labelledby="perspective-title" className="rounded-2xl border border-line bg-white p-7 shadow-sm sm:p-9">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted">Perspectiva de negócio</p>
              <h2 id="perspective-title" className="mt-5 text-2xl font-semibold leading-snug tracking-tight text-navy">Aprovar crédito é avaliar um equilíbrio.</h2>
              <p className="mt-4 text-sm leading-7 text-muted">Critérios de aprovação influenciam o volume de operações e o risco assumido. Entender esse compromisso exige avaliar os dados e tornar as hipóteses visíveis.</p>
              <div className="mt-7 border-t border-line pt-6">
                <p className="text-sm font-semibold text-navy">Evidência antes de conclusão</p>
                <p className="mt-2 text-sm leading-6 text-muted">A apresentação de resultados reais depende de artefatos verificados e de sua procedência.</p>
              </div>
            </aside>
          </div>
        </section>

        <section id="abordagem" aria-labelledby="approach-title" className="mx-auto max-w-7xl scroll-mt-6 px-6 py-16 sm:px-10 lg:px-14">
          <div className="max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-teal">Da origem à decisão</p>
            <h2 id="approach-title" className="mt-3 text-3xl font-semibold tracking-tight text-navy">Uma abordagem conectada.</h2>
            <p className="mt-4 leading-7 text-muted">O projeto Python reúne etapas complementares para examinar o problema de crédito, das verificações de qualidade à comparação de cenários.</p>
          </div>
          <div className="mt-9 grid gap-5 md:grid-cols-3">
            {approach.map((item) => (
              <article key={item.title} className="rounded-xl border border-line bg-white p-7">
                <p className="text-xs font-medium text-teal">{item.detail}</p>
                <h3 className="mt-4 text-xl font-semibold tracking-tight text-navy">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-muted">{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="transparencia" aria-labelledby="transparency-title" className="mx-auto max-w-7xl scroll-mt-6 px-6 pb-16 sm:px-10 lg:px-14">
          <div className="grid gap-6 rounded-2xl bg-navy p-7 text-white sm:p-10 md:grid-cols-[1fr_1.4fr] md:gap-12">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-teal-light">Transparência</p>
              <h2 id="transparency-title" className="mt-4 text-2xl font-semibold tracking-tight">Contexto faz parte do resultado.</h2>
            </div>
            <div className="space-y-4 text-sm leading-7 text-slate-200">
              <p>A demonstração local em Streamlit utiliza dados inteiramente sintéticos. Eles ilustram o funcionamento do projeto e não demonstram desempenho bancário.</p>
              <p>Resultados reais ainda não estão disponíveis nesta apresentação. Simulações dependem de hipóteses; suas margens antes de custos não representam lucro.</p>
              <p className="border-t border-white/20 pt-4 text-xs text-slate-300">Uso educacional e de portfólio. A apresentação web está em desenvolvimento.</p>
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 py-7 text-xs text-muted sm:flex-row sm:items-center sm:justify-between sm:px-10 lg:px-14">
          <p className="font-semibold text-navy">Credit Risk Intelligence</p>
          <p>Análise com contexto. Decisões com hipóteses explícitas.</p>
          <a className="w-fit underline decoration-line underline-offset-4 hover:text-navy" href="#projeto">Voltar ao início ↑</a>
        </div>
      </footer>
    </>
  );
}
