import React, { useState, useEffect } from "react";
import { useApi } from "../../api/withAuthClient";
import "./ServicesPage.css";

const ServicesPage = () => {
  const api = useApi();
  const [insuranceNumber, setInsuranceNumber] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [patientData, setPatientData] = useState({
    patientInfo: null,
    medicines: null,
    notes: null,
    labReports: null,
  });
  const [detailedMedicines, setDetailedMedicines] = useState(null);
  const [detailedNotes, setDetailedNotes] = useState(null);
  const [detailedLabReports, setDetailedLabReports] = useState(null);
  const [medicinesLoading, setMedicinesLoading] = useState(false);
  const [notesLoading, setNotesLoading] = useState(false);
  const [labReportsLoading, setLabReportsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [currentNotesPage, setCurrentNotesPage] = useState(1);
  const [currentLabReportsPage, setCurrentLabReportsPage] = useState(1);
  const [itemsPerPage] = useState(2);
  const [labReportsPerPage] = useState(1);

  // Add Patient Form State
  const [showAddPatientForm, setShowAddPatientForm] = useState(false);
  const [addPatientLoading, setAddPatientLoading] = useState(false);
  const [addPatientError, setAddPatientError] = useState("");
  const [addPatientForm, setAddPatientForm] = useState({
    firstName: "",
    lastName: "",
    dateOfBirth: "",
    insuranceNumber: "",
    address: "",
    phoneNumber: "",
    email: "",
  });

  // ADD Data Form State
  const [showAddDataForm, setShowAddDataForm] = useState(false);
  const [addDataLoading, setAddDataLoading] = useState(false);
  const [addDataError, setAddDataError] = useState("");
  const [addDataSuccess, setAddDataSuccess] = useState("");

  // Medicine Form State
  const [medicines, setMedicines] = useState([
    {
      name: "",
      dosage: "",
      frequency: "",
      startDate: "",
      endDate: "",
      instructions: "",
    },
  ]);

  // Notes Form State
  const [notes, setNotes] = useState("");

  // File Upload State
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // AI Summary State
  const [aiSummary, setAiSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState("");

  // Fetch detailed medicines when Medicines tab is selected
  useEffect(() => {
    if (
      activeTab === "medicines" &&
      patientData.patientInfo &&
      !detailedMedicines
    ) {
      fetchDetailedMedicines();
    }
  }, [activeTab, patientData.patientInfo, detailedMedicines]);

  // Fetch detailed notes when Notes tab is selected
  useEffect(() => {
    if (activeTab === "notes" && patientData.patientInfo && !detailedNotes) {
      fetchDetailedNotes();
    }
  }, [activeTab, patientData.patientInfo, detailedNotes]);

  // Fetch detailed lab reports when Lab Reports tab is selected
  useEffect(() => {
    if (
      activeTab === "labReports" &&
      patientData.patientInfo &&
      !detailedLabReports
    ) {
      fetchDetailedLabReports();
    }
  }, [activeTab, patientData.patientInfo, detailedLabReports]);

  const tabs = [
    { id: "all", label: "All" },
    { id: "medicines", label: "Medicines" },
    { id: "notes", label: "Notes" },
    { id: "labReports", label: "Lab Reports" },
  ];

  const fetchDetailedMedicines = async () => {
    if (!insuranceNumber.trim()) return;

    setMedicinesLoading(true);
    try {
      const response = await api.get(
        `/api/medicine/getMedicines/${insuranceNumber}`
      );
      setDetailedMedicines(response);
      setCurrentPage(1); // Reset to first page when new data is loaded
    } catch (err) {
      console.error("Failed to fetch detailed medicines:", err);
    } finally {
      setMedicinesLoading(false);
    }
  };

  const fetchDetailedNotes = async () => {
    if (!insuranceNumber.trim()) return;

    setNotesLoading(true);
    try {
      const response = await api.get(
        `/api/doctornotes/getnotes/${insuranceNumber}`
      );
      setDetailedNotes(response);
      setCurrentNotesPage(1); // Reset to first page when new data is loaded
    } catch (err) {
      console.error("Failed to fetch detailed notes:", err);
    } finally {
      setNotesLoading(false);
    }
  };

  const fetchDetailedLabReports = async () => {
    if (!insuranceNumber.trim()) return;

    setLabReportsLoading(true);
    try {
      const response = await api.get(
        `/api/labreport/getLabReport/${insuranceNumber}`
      );
      setDetailedLabReports(response);
      setCurrentLabReportsPage(1); // Reset to first page when new data is loaded
    } catch (err) {
      console.error("Failed to fetch detailed lab reports:", err);
    } finally {
      setLabReportsLoading(false);
    }
  };

  const searchPatient = async () => {
    if (!insuranceNumber.trim()) {
      setError("Please enter an insurance number");
      return;
    }

    setLoading(true);
    setError("");
    setShowAddPatientForm(false);
    setAddPatientError("");
    setPatientData({
      patientInfo: null,
      medicines: null,
      notes: null,
      labReports: null,
    });
    setDetailedMedicines(null);
    setDetailedNotes(null);
    setDetailedLabReports(null);
    setCurrentPage(1);
    setCurrentNotesPage(1);
    setCurrentLabReportsPage(1);

    try {
      // Fetch all data in parallel
      const [patientInfoRes, medicinesRes, notesRes, labReportsRes] =
        await Promise.allSettled([
          api.get(`/api/patient/get/${insuranceNumber}`),
          api.get(`/api/medicine/getLast5Medicines/${insuranceNumber}`),
          api.get(`/api/doctornotes/getlatestnotes/${insuranceNumber}`),
          api.get(`/api/labreport/getLatestLabReport/${insuranceNumber}`),
        ]);

      const newData = {
        patientInfo:
          patientInfoRes.status === "fulfilled" ? patientInfoRes.value : null,
        medicines:
          medicinesRes.status === "fulfilled" ? medicinesRes.value : null,
        notes: notesRes.status === "fulfilled" ? notesRes.value : null,
        labReports:
          labReportsRes.status === "fulfilled" ? labReportsRes.value : null,
      };

      setPatientData(newData);
    } catch (err) {
      setError(err.message || "Failed to fetch patient data");
    } finally {
      setLoading(false);
    }
  };

  const addPatient = async (e) => {
    e.preventDefault();

    if (
      !addPatientForm.firstName.trim() ||
      !addPatientForm.lastName.trim() ||
      !addPatientForm.dateOfBirth ||
      !addPatientForm.insuranceNumber.trim() ||
      !addPatientForm.address.trim() ||
      !addPatientForm.phoneNumber.trim() ||
      !addPatientForm.email.trim()
    ) {
      setAddPatientError("All fields are required");
      return;
    }

    setAddPatientLoading(true);
    setAddPatientError("");

    try {
      const response = await api.post("/api/patient/add", addPatientForm);

      if (response) {
        // Reset form and hide it
        setShowAddPatientForm(false);
        setAddPatientForm({
          firstName: "",
          lastName: "",
          dateOfBirth: "",
          insuranceNumber: "",
          address: "",
          phoneNumber: "",
          email: "",
        });

        // Reload patient data
        await searchPatient();
      }
    } catch (err) {
      setAddPatientError(err.message || "Failed to add patient");
    } finally {
      setAddPatientLoading(false);
    }
  };

  const handleAddPatientFormChange = (e) => {
    const { name, value } = e.target;
    setAddPatientForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const openAddPatientForm = () => {
    setAddPatientForm((prev) => ({
      ...prev,
      insuranceNumber: insuranceNumber,
    }));
    setShowAddPatientForm(true);
    setAddPatientError("");
  };

  // ADD Data Functions
  const openAddDataForm = () => {
    setShowAddDataForm(true);
    setAddDataError("");
    setAddDataSuccess("");
    setMedicines([
      {
        name: "",
        dosage: "",
        frequency: "",
        startDate: "",
        endDate: "",
        instructions: "",
      },
    ]);
    setNotes("");
    setSelectedFile(null);
    setUploadProgress(0);
  };

  const addMedicineRow = () => {
    setMedicines((prev) => [
      ...prev,
      {
        name: "",
        dosage: "",
        frequency: "",
        startDate: "",
        endDate: "",
        instructions: "",
      },
    ]);
  };

  const removeMedicineRow = (index) => {
    if (medicines.length > 1) {
      setMedicines((prev) => prev.filter((_, i) => i !== index));
    }
  };

  const updateMedicine = (index, field, value) => {
    setMedicines((prev) =>
      prev.map((medicine, i) =>
        i === index ? { ...medicine, [field]: value } : medicine
      )
    );
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === "application/pdf") {
      setSelectedFile(file);
      setAddDataError("");
    } else {
      setAddDataError("Please select a valid PDF file");
      setSelectedFile(null);
    }
  };

  const getAiSummary = async () => {
    if (!insuranceNumber.trim()) return;

    setSummaryLoading(true);
    setSummaryError("");
    setAiSummary(null);

    try {
      const response = await api.get(
        `/api/summary/getSummary/${insuranceNumber}`
      );
      setAiSummary(response);
    } catch (err) {
      setSummaryError(err.message || "Failed to fetch AI summary");
    } finally {
      setSummaryLoading(false);
    }
  };

  const submitAddData = async (e) => {
    e.preventDefault();

    // Validate medicines
    const validMedicines = medicines.filter(
      (med) =>
        med.name.trim() &&
        med.dosage.trim() &&
        med.frequency.trim() &&
        med.startDate &&
        med.endDate &&
        med.instructions.trim()
    );

    if (validMedicines.length === 0 && !notes.trim() && !selectedFile) {
      setAddDataError(
        "Please fill at least one section (medicines, notes, or upload file)"
      );
      return;
    }

    setAddDataLoading(true);
    setAddDataError("");
    setAddDataSuccess("");

    try {
      const promises = [];

      // Add medicines if any
      if (validMedicines.length > 0) {
        promises.push(
          api.post(
            `/api/medicine/addMedicine/${insuranceNumber}`,
            validMedicines
          )
        );
      }

      // Add notes if any
      if (notes.trim()) {
        promises.push(
          api.post(`/api/doctornotes/uploadnotes/${insuranceNumber}`, {
            notes: notes.trim(),
          })
        );
      }

      // Upload file if any
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);

        promises.push(
          api.post(`/api/labreport/upload/${insuranceNumber}`, formData, {
            onUploadProgress: (progressEvent) => {
              const progress = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setUploadProgress(progress);
            },
          })
        );
      }

      // Wait for all operations to complete
      await Promise.all(promises);

      setAddDataSuccess("Data added successfully!");

      // Reset form
      setTimeout(() => {
        setShowAddDataForm(false);
        setMedicines([
          {
            name: "",
            dosage: "",
            frequency: "",
            startDate: "",
            endDate: "",
            instructions: "",
          },
        ]);
        setNotes("");
        setSelectedFile(null);
        setUploadProgress(0);
        setAddDataSuccess("");

        // Reload patient data to show updates
        searchPatient();
      }, 2000);
    } catch (err) {
      setAddDataError(err.message || "Failed to add data");
    } finally {
      setAddDataLoading(false);
    }
  };

  const renderPatientInfo = () => {
    if (!patientData.patientInfo) {
      return (
        <div className="no-data">
          <p>No patient information available for this insurance number</p>
          <button onClick={openAddPatientForm} className="add-patient-btn">
            Add Patient
          </button>
        </div>
      );
    }

    const { firstName, lastName, dateOfBirth, address, phoneNumber } =
      patientData.patientInfo;
    const fullName = `${firstName} ${lastName}`;
    const formattedDate = new Date(dateOfBirth).toLocaleDateString();

    return (
      <div className="section">
        <h3>Patient Information</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Insurance Number</th>
              <th>Full Name</th>
              <th>Date of Birth</th>
              <th>Address</th>
              <th>Phone Number</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{insuranceNumber}</td>
              <td>{fullName}</td>
              <td>{formattedDate}</td>
              <td>{address}</td>
              <td>{phoneNumber}</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  };

  const renderDetailedMedicinesTable = () => {
    if (!detailedMedicines || detailedMedicines.length === 0) {
      return (
        <div className="no-data">
          No detailed medicine data available for this patient
        </div>
      );
    }

    // Group medicines by date for pagination
    const allDateGroups = [];
    detailedMedicines.forEach((dateGroup) => {
      allDateGroups.push({
        date: dateGroup.date,
        medicines: dateGroup.medicines,
      });
    });

    // Calculate pagination based on date groups
    const totalPages = Math.ceil(allDateGroups.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentDateGroups = allDateGroups.slice(startIndex, endIndex);

    const getMedicineStatus = (startDate, endDate) => {
      const today = new Date();
      const start = new Date(startDate);
      const end = new Date(endDate);

      if (start > today) {
        return "Yet to start";
      } else if (end < today) {
        return "Completed";
      } else {
        return "Ongoing";
      }
    };

    const handlePageChange = (page) => {
      setCurrentPage(page);
    };

    return (
      <div className="section">
        <h3>All Medicines</h3>

        {currentDateGroups.map((dateGroup, groupIndex) => (
          <div key={groupIndex} className="date-group">
            <h4 className="date-header">Prescription Date: {dateGroup.date}</h4>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Dosage</th>
                  <th>Frequency</th>
                  <th>Status</th>
                  <th>Instructions</th>
                </tr>
              </thead>
              <tbody>
                {dateGroup.medicines.map((medicine, index) => (
                  <tr key={index}>
                    <td>{medicine.name}</td>
                    <td>{medicine.dosage}</td>
                    <td>{medicine.frequency}</td>
                    <td>
                      {getMedicineStatus(medicine.startDate, medicine.endDate)}
                    </td>
                    <td>{medicine.instructions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="pagination-btn"
            >
              Previous
            </button>
            <span className="pagination-info">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="pagination-btn"
            >
              Next
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderDetailedNotesTable = () => {
    if (!detailedNotes || detailedNotes.length === 0) {
      return (
        <div className="no-data">
          No detailed notes data available for this patient
        </div>
      );
    }

    // Group notes by date for pagination
    const allDateGroups = [];
    detailedNotes.forEach((dateGroup) => {
      allDateGroups.push({
        date: dateGroup.date,
        doctornotes: dateGroup.doctornotes,
      });
    });

    // Calculate pagination based on date groups
    const totalPages = Math.ceil(allDateGroups.length / itemsPerPage);
    const startIndex = (currentNotesPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentDateGroups = allDateGroups.slice(startIndex, endIndex);

    const handleNotesPageChange = (page) => {
      setCurrentNotesPage(page);
    };

    return (
      <div className="section">
        <h3>All Doctor Notes</h3>

        {currentDateGroups.map((dateGroup, groupIndex) => (
          <div key={groupIndex} className="date-group">
            <h4 className="date-header">Date: {dateGroup.date}</h4>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {dateGroup.doctornotes.map((note, index) => (
                  <tr key={index}>
                    <td>{note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            <button
              onClick={() => handleNotesPageChange(currentNotesPage - 1)}
              disabled={currentNotesPage === 1}
              className="pagination-btn"
            >
              Previous
            </button>
            <span className="pagination-info">
              Page {currentNotesPage} of {totalPages}
            </span>
            <button
              onClick={() => handleNotesPageChange(currentNotesPage + 1)}
              disabled={currentNotesPage === totalPages}
              className="pagination-btn"
            >
              Next
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderDetailedLabReportsTable = () => {
    if (!detailedLabReports || detailedLabReports.length === 0) {
      return (
        <div className="no-data">
          No detailed lab report data available for this patient
        </div>
      );
    }

    // Group lab reports by date for pagination
    const allDateGroups = [];
    detailedLabReports.forEach((dateGroup) => {
      allDateGroups.push({
        date: dateGroup.uploadDate,
        labReports: dateGroup.labReports,
      });
    });

    // Calculate pagination based on date groups - 1 date per page
    console.log("Debug pagination:", {
      allDateGroupsLength: allDateGroups.length,
      labReportsPerPage,
      totalPages: Math.ceil(allDateGroups.length / labReportsPerPage),
    });
    const totalPages = Math.ceil(allDateGroups.length / labReportsPerPage);
    const startIndex = (currentLabReportsPage - 1) * labReportsPerPage;
    const endIndex = startIndex + labReportsPerPage;
    const currentDateGroups = allDateGroups.slice(startIndex, endIndex);

    const handleLabReportsPageChange = (page) => {
      setCurrentLabReportsPage(page);
    };

    return (
      <div className="section">
        <h3>All Lab Reports</h3>

        {currentDateGroups.map((dateGroup, groupIndex) => (
          <div key={groupIndex} className="date-group">
            <h4 className="date-header">Upload Date: {dateGroup.date}</h4>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Test Name</th>
                  <th>Value</th>
                  <th>Unit</th>
                  <th>Reference Range</th>
                </tr>
              </thead>
              <tbody>
                {dateGroup.labReports.map((report, index) => (
                  <tr key={index}>
                    <td>{report.testName}</td>
                    <td>{report.value || "N/A"}</td>
                    <td>{report.unit || "N/A"}</td>
                    <td>{report.referenceRange || "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}

        {/* Pagination */}
        {console.log("Lab Reports Pagination condition:", {
          totalPages,
          shouldShow: totalPages > 1,
        })}
        {/* Temporarily show pagination for debugging */}
        {true && (
          <div className="pagination">
            <button
              onClick={() =>
                handleLabReportsPageChange(currentLabReportsPage - 1)
              }
              disabled={currentLabReportsPage === 1}
              className="pagination-btn"
            >
              Previous
            </button>
            <span className="pagination-info">
              Page {currentLabReportsPage} of {totalPages}
            </span>
            <button
              onClick={() =>
                handleLabReportsPageChange(currentLabReportsPage + 1)
              }
              disabled={currentLabReportsPage === totalPages}
              className="pagination-btn"
            >
              Next
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderMedicinesTable = () => {
    if (!patientData.medicines) {
      return (
        <div className="no-data">
          No medicine data available for this patient
        </div>
      );
    }

    const { date, medicines } = patientData.medicines;
    if (!medicines || medicines.length === 0) {
      return (
        <div className="no-data">
          No medicine data available for this patient
        </div>
      );
    }

    const getMedicineStatus = (startDate, endDate) => {
      const today = new Date();
      const start = new Date(startDate);
      const end = new Date(endDate);

      if (start > today) {
        return "Yet to start";
      } else if (end < today) {
        return "Completed";
      } else {
        return "Ongoing";
      }
    };

    return (
      <div className="section">
        <h3>Last 5 Medicines - {date}</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Dosage</th>
              <th>Frequency</th>
              <th>Status</th>
              <th>Instructions</th>
            </tr>
          </thead>
          <tbody>
            {medicines.map((medicine, index) => (
              <tr key={index}>
                <td>{medicine.name}</td>
                <td>{medicine.dosage}</td>
                <td>{medicine.frequency}</td>
                <td>
                  {getMedicineStatus(medicine.startDate, medicine.endDate)}
                </td>
                <td>{medicine.instructions}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderNotesTable = () => {
    if (!patientData.notes) {
      return (
        <div className="no-data">No notes data available for this patient</div>
      );
    }

    const { date, doctornotes } = patientData.notes;
    if (!doctornotes || doctornotes.length === 0) {
      return (
        <div className="no-data">No notes data available for this patient</div>
      );
    }

    return (
      <div className="section">
        <h3>Latest Doctor Notes - {date}</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {doctornotes.map((note, index) => (
              <tr key={index}>
                <td>{note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderLabReportsTable = () => {
    if (!patientData.labReports) {
      return (
        <div className="no-data">
          No lab reports data available for this patient
        </div>
      );
    }

    const { uploadDate, labReports } = patientData.labReports;
    if (!labReports || labReports.length === 0) {
      return (
        <div className="no-data">
          No lab reports data available for this patient
        </div>
      );
    }

    return (
      <div className="section">
        <h3>Latest Lab Report - {uploadDate}</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Test Name</th>
              <th>Value</th>
              <th>Unit</th>
              <th>Reference Range</th>
            </tr>
          </thead>
          <tbody>
            {labReports.map((report, index) => (
              <tr key={index}>
                <td>{report.testName}</td>
                <td>{report.value}</td>
                <td>{report.unit}</td>
                <td>{report.referenceRange || "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderAllData = () => {
    return (
      <div className="all-sections">
        {renderPatientInfo()}
        {renderMedicinesTable()}
        {renderNotesTable()}
        {renderLabReportsTable()}
      </div>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "medicines":
        return (
          <div className="all-sections">
            {renderPatientInfo()}
            {detailedMedicines
              ? renderDetailedMedicinesTable()
              : renderMedicinesTable()}
          </div>
        );
      case "notes":
        return (
          <div className="all-sections">
            {renderPatientInfo()}
            {detailedNotes ? renderDetailedNotesTable() : renderNotesTable()}
          </div>
        );
      case "labReports":
        return (
          <div className="all-sections">
            {renderPatientInfo()}
            {detailedLabReports
              ? renderDetailedLabReportsTable()
              : renderLabReportsTable()}
          </div>
        );
      default:
        return renderAllData();
    }
  };

  return (
    <div className="services-page">
      <div className="search-section">
        <h2>Patient Record Search</h2>
        <div className="search-container">
          <input
            type="text"
            placeholder="Enter Insurance Number"
            value={insuranceNumber}
            onChange={(e) => setInsuranceNumber(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && searchPatient()}
            className="search-input"
          />
          <button
            onClick={searchPatient}
            disabled={loading}
            className="search-button"
          >
            {loading ? "Searching..." : "Search"}
          </button>
          {patientData.patientInfo !== null && (
            <>
              <button onClick={openAddDataForm} className="add-data-button">
                Add Data
              </button>
              <button onClick={getAiSummary} className="ai-summary-button">
                {summaryLoading ? "Getting Summary..." : "AI Summary"}
              </button>
            </>
          )}
        </div>
        {error && <div className="error-message">{error}</div>}
      </div>

      {patientData.patientInfo !== null && (
        <>
          <div className="tabs-section">
            <div className="tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`tab ${activeTab === tab.id ? "active" : ""}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="tab-content">{renderTabContent()}</div>
          </div>
        </>
      )}

      {/* Add Patient Form Overlay */}
      {showAddPatientForm && (
        <div className="add-patient-form-overlay">
          <div className="add-patient-form-content">
            <h3>Add New Patient</h3>
            <form onSubmit={addPatient}>
              <div className="form-group">
                <label>First Name:</label>
                <input
                  type="text"
                  name="firstName"
                  value={addPatientForm.firstName}
                  onChange={handleAddPatientFormChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Last Name:</label>
                <input
                  type="text"
                  name="lastName"
                  value={addPatientForm.lastName}
                  onChange={handleAddPatientFormChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Date of Birth:</label>
                <input
                  type="date"
                  name="dateOfBirth"
                  value={addPatientForm.dateOfBirth}
                  onChange={handleAddPatientFormChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Insurance Number:</label>
                <input
                  type="text"
                  name="insuranceNumber"
                  value={addPatientForm.insuranceNumber}
                  onChange={handleAddPatientFormChange}
                  required
                  disabled
                />
              </div>
              <div className="form-group">
                <label>Address:</label>
                <input
                  type="text"
                  name="address"
                  value={addPatientForm.address}
                  onChange={handleAddPatientFormChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Phone Number:</label>
                <input
                  type="text"
                  name="phoneNumber"
                  value={addPatientForm.phoneNumber}
                  onChange={handleAddPatientFormChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email:</label>
                <input
                  type="email"
                  name="email"
                  value={addPatientForm.email}
                  onChange={handleAddPatientFormChange}
                  required
                />
              </div>
              <button type="submit" disabled={addPatientLoading}>
                {addPatientLoading ? "Adding..." : "Add Patient"}
              </button>
              {addPatientError && (
                <div className="error-message">{addPatientError}</div>
              )}
            </form>
            <button
              onClick={() => setShowAddPatientForm(false)}
              className="close-btn"
            >
              X
            </button>
          </div>
        </div>
      )}

      {/* Add Data Form Overlay */}
      {showAddDataForm && (
        <div className="add-data-form-overlay">
          <div className="add-data-form-content">
            <h3>Add New Data for {insuranceNumber}</h3>
            <form onSubmit={submitAddData}>
              <div className="form-group">
                <label>Medicines:</label>
                {medicines.map((medicine, index) => (
                  <div key={index} className="medicine-row">
                    <div className="medicine-inputs">
                      <input
                        type="text"
                        placeholder="Medicine Name"
                        value={medicine.name}
                        onChange={(e) =>
                          updateMedicine(index, "name", e.target.value)
                        }
                      />
                      <input
                        type="text"
                        placeholder="Dosage"
                        value={medicine.dosage}
                        onChange={(e) =>
                          updateMedicine(index, "dosage", e.target.value)
                        }
                      />
                      <input
                        type="text"
                        placeholder="Frequency"
                        value={medicine.frequency}
                        onChange={(e) =>
                          updateMedicine(index, "frequency", e.target.value)
                        }
                      />
                      <input
                        type="date"
                        value={medicine.startDate}
                        onChange={(e) =>
                          updateMedicine(index, "startDate", e.target.value)
                        }
                      />
                      <input
                        type="date"
                        value={medicine.endDate}
                        onChange={(e) =>
                          updateMedicine(index, "endDate", e.target.value)
                        }
                      />
                    </div>
                    <textarea
                      placeholder="Instructions"
                      value={medicine.instructions}
                      onChange={(e) =>
                        updateMedicine(index, "instructions", e.target.value)
                      }
                    />
                    {medicines.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeMedicineRow(index)}
                        className="remove-medicine-btn"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addMedicineRow}
                  className="add-medicine-btn"
                >
                  + Add Another Medicine
                </button>
              </div>
              <div className="form-group">
                <label>Notes:</label>
                <textarea
                  name="notes"
                  placeholder="Enter your notes here..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Upload Lab Report (PDF only):</label>
                <input
                  type="file"
                  name="labReportFile"
                  accept=".pdf"
                  onChange={handleFileChange}
                />
                {selectedFile && <p>Selected file: {selectedFile.name}</p>}
                {uploadProgress > 0 && (
                  <p>Upload progress: {uploadProgress}%</p>
                )}
              </div>
              <button type="submit" disabled={addDataLoading}>
                {addDataLoading ? "Adding..." : "Add Data"}
              </button>
              {addDataError && (
                <div className="error-message">{addDataError}</div>
              )}
              {addDataSuccess && (
                <div className="success-message">{addDataSuccess}</div>
              )}
            </form>
            <button
              onClick={() => setShowAddDataForm(false)}
              className="close-btn"
            >
              X
            </button>
          </div>
        </div>
      )}

      {/* AI Summary Form Overlay */}
      {(aiSummary || summaryLoading) && (
        <div className="ai-summary-form-overlay">
          <div className="ai-summary-form-content">
            <h3>AI Summary</h3>
            {summaryError && (
              <div className="error-message">{summaryError}</div>
            )}
            {aiSummary ? (
              <div className="summary-content">
                <p>{aiSummary}</p>
              </div>
            ) : (
              <div className="no-summary">
                {summaryLoading ? (
                  <p>Generating AI summary...</p>
                ) : (
                  <p>
                    Click "Get AI Summary" to generate a summary of patient data
                  </p>
                )}
              </div>
            )}
            <button
              onClick={() => {
                setAiSummary(null);
                setSummaryError("");
              }}
              className="close-btn"
            >
              X
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ServicesPage;
