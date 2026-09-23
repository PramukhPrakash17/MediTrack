import React from "react";
import "./ReferencesPage.css";

const referenceGroups = [
  {
    title: "Drug RAG",
    description:
      "Data sources used to build the drug information / medication retrieval knowledge base.",
    items: [
      {
        name: "250k Medicines Usage, Side Effects and Substitutes",
        source: "Kaggle",
        url: "https://www.kaggle.com/datasets/shudhanshusingh/250k-medicines-usage-side-effects-and-substitutes",
      },
      {
        name: "Drugs, Side Effects and Medical Condition",
        source: "Kaggle",
        url: "https://www.kaggle.com/datasets/jithinanievarghese/drugs-side-effects-and-medical-condition",
      },
    ],
  },
  {
    title: "Disease RAG",
    description:
      "Data sources used to build the disease information / diagnosis retrieval knowledge base.",
    items: [
      {
        name: "The Gale Encyclopedia of Medicine",
        source: "PDF (reference text)",
        url: null,
      },
    ],
  },
];

const ReferencesPage = () => {
  return (
    <div className="services-page references-page">
      <div className="search-section">
        <h2>References</h2>
        <p className="references-subtitle">
          Data sources used for quality assurance of the Disease and Drug
          RAG knowledge bases.
        </p>
      </div>

      {referenceGroups.map((group) => (
        <div className="reference-group" key={group.title}>
          <h3 className="reference-group-title">{group.title}</h3>
          <p className="reference-group-description">{group.description}</p>
          <ul className="reference-list">
            {group.items.map((item) => (
              <li className="reference-item" key={item.name}>
                <div className="reference-item-name">{item.name}</div>
                <div className="reference-item-meta">
                  <span className="reference-item-source">{item.source}</span>
                  {item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="reference-item-link"
                    >
                      {item.url}
                    </a>
                  ) : (
                    <span className="reference-item-no-link">
                      Link not published
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
};

export default ReferencesPage;
