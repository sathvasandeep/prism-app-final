import React from "react";

// Placeholder for radar chart component (to be implemented)
const RadarChart = ({ title, data }: { title: string; data: any }) => (
  <div style={{ width: 400, margin: 20 }}>
    <h3>{title}</h3>
    {/* TODO: Replace with actual radar chart */}
    <div style={{ height: 300, background: "#f5f5f5", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <span>Radar Chart Placeholder</span>
    </div>
  </div>
);

const Stage3: React.FC = () => {
  // TODO: Fetch SKIVE radar data, archetype info, profession info from backend
  // Placeholder data:
  const radarData = {
    skills: {},
    knowledge: {},
    identity: {},
    values: {},
    ethics: {},
    combined: {},
  };
  const archetype = {
    name: "Diplomatic Prioritizer",
    narrative: "This role operates at a strategic level, where success is defined by a mastery of Prioritization and Stakeholder Management...",
    globalName: "Strategic Leader",
  };
  const professionInfo = {
    title: "Senior Product Manager",
    summary: "A senior PM leads cross-functional teams to deliver business value...",
    yearsToRole: 8,
    qualifications: ["MBA", "PMP Certification"],
    certifications: ["Scrum Master", "Product Owner"],
    salaryRange: "₹25-60LPA",
    perks: ["Stock options", "Remote work"],
    highs: "Influence, Impact, Compensation",
    lows: "Stress, Politics, Uncertainty",
    videoUrl: "https://www.youtube.com/embed/example",
    careerPathway: "Associate PM → PM → Senior PM → Director"
  };

  return (
    <div style={{ padding: 32 }}>
      <h1>Stage 3: Role DNA Archetype</h1>
      <section style={{ marginBottom: 32 }}>
        <h2>Profile: {professionInfo.title}</h2>
        <p>{professionInfo.summary}</p>
        <ul>
          <li><b>Years to Role:</b> {professionInfo.yearsToRole}</li>
          <li><b>Qualifications:</b> {professionInfo.qualifications.join(", ")}</li>
          <li><b>Certifications:</b> {professionInfo.certifications.join(", ")}</li>
          <li><b>Salary Range:</b> {professionInfo.salaryRange}</li>
          <li><b>Perks:</b> {professionInfo.perks.join(", ")}</li>
          <li><b>Highs:</b> {professionInfo.highs}</li>
          <li><b>Lows:</b> {professionInfo.lows}</li>
          <li><b>Career Pathway:</b> {professionInfo.careerPathway}</li>
        </ul>
        <div style={{ marginTop: 20 }}>
          <iframe
            width="420"
            height="236"
            src={professionInfo.videoUrl}
            title="Profession Video"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          ></iframe>
        </div>
      </section>
      <section style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 32 }}>
        <RadarChart title="Skills" data={radarData.skills} />
        <RadarChart title="Knowledge" data={radarData.knowledge} />
        <RadarChart title="Identity" data={radarData.identity} />
        <RadarChart title="Values" data={radarData.values} />
        <RadarChart title="Ethics" data={radarData.ethics} />
        <RadarChart title="Combined SKIVE" data={radarData.combined} />
      </section>
      <section>
        <h2>Archetype: {archetype.name}</h2>
        <h3>Global Archetype: {archetype.globalName}</h3>
        <p>{archetype.narrative}</p>
      </section>
    </div>
  );
};

export default Stage3;
