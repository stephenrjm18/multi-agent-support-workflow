"use client";

import { FormEvent, useState } from "react";

type Approval = {
  type: string;
  message: string;
  action: string | null;
  amount: number | null;
  reason: string | null;
  next_step: string | null;
  options: string[];
};

type SupportResponse = {
  thread_id: string;
  status: "awaiting_approval" | "completed";
  message: string;
  approval_required: boolean;
  approval: Approval | null;
  final_response: string | null;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export default function Home() {
  const [customerId, setCustomerId] = useState("1");
  const [userRequest, setUserRequest] = useState(
    "I want a refund for order 1001"
  );

  const [result, setResult] =
    useState<SupportResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [approvalLoading, setApprovalLoading] =
    useState(false);

  const [error, setError] = useState("");

  async function submitRequest(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/support/request`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_request: userRequest,
            customer_id: Number(customerId),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to submit support request."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  async function submitApproval(
    decision: "approve" | "reject"
  ) {
    if (!result) {
      return;
    }

    setApprovalLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/support/request/${result.thread_id}/approval`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            decision,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to continue workflow."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      );
    } finally {
      setApprovalLoading(false);
    }
  }

  function resetRequest() {
    setResult(null);
    setError("");
  }

  return (
    <main className="page">
      <section className="container">
        <header className="header">
          <div>
            <p className="eyebrow">
              GENAI SUPPORT PLATFORM
            </p>

            <h1>
              AI Customer Support Assistant
            </h1>

            <p className="subtitle">
              Multi-agent support automation with
              human approval and QA validation.
            </p>
          </div>
        </header>

        <section className="card">
          <h2>Submit Support Request</h2>

          <form onSubmit={submitRequest}>
            <label htmlFor="customerId">
              Customer ID
            </label>

            <input
              id="customerId"
              type="number"
              min="1"
              value={customerId}
              onChange={(event) =>
                setCustomerId(event.target.value)
              }
              required
            />

            <label htmlFor="userRequest">
              Support Request
            </label>

            <textarea
              id="userRequest"
              value={userRequest}
              onChange={(event) =>
                setUserRequest(event.target.value)
              }
              rows={5}
              required
            />

            <button
              className="primaryButton"
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Processing..."
                : "Submit Request"}
            </button>
          </form>
        </section>

        {error && (
          <section className="card errorCard">
            <h2>Error</h2>
            <p>{error}</p>
          </section>
        )}

        {result && (
          <section className="card">
            <div className="statusHeader">
              <div>
                <p className="eyebrow">
                  WORKFLOW STATUS
                </p>

                <h2>
                  {result.status ===
                  "awaiting_approval"
                    ? "Awaiting Human Approval"
                    : "Request Completed"}
                </h2>
              </div>

              <span
                className={`status ${
                  result.status ===
                  "awaiting_approval"
                    ? "pending"
                    : "completed"
                }`}
              >
                {result.status ===
                "awaiting_approval"
                  ? "Pending"
                  : "Completed"}
              </span>
            </div>

            <p className="message">
              {result.message}
            </p>

            {result.approval_required &&
              result.approval && (
                <div className="approvalBox">
                  <h3>
                    Human Approval Required
                  </h3>

                  <p>
                    {result.approval.message}
                  </p>

                  <div className="details">
                    {result.approval.action && (
                      <div>
                        <span>Action</span>
                        <strong>
                          {result.approval.action}
                        </strong>
                      </div>
                    )}

                    {result.approval.amount !==
                      null && (
                      <div>
                        <span>Amount</span>
                        <strong>
                          $
                          {result.approval.amount.toFixed(
                            2
                          )}
                        </strong>
                      </div>
                    )}

                    {result.approval.reason && (
                      <div>
                        <span>Reason</span>
                        <strong>
                          {result.approval.reason}
                        </strong>
                      </div>
                    )}

                    {result.approval.next_step && (
                      <div>
                        <span>Next Step</span>
                        <strong>
                          {
                            result.approval
                              .next_step
                          }
                        </strong>
                      </div>
                    )}
                  </div>

                  <div className="approvalButtons">
                    <button
                      className="approveButton"
                      onClick={() =>
                        submitApproval("approve")
                      }
                      disabled={approvalLoading}
                    >
                      {approvalLoading
                        ? "Processing..."
                        : "Approve"}
                    </button>

                    <button
                      className="rejectButton"
                      onClick={() =>
                        submitApproval("reject")
                      }
                      disabled={approvalLoading}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              )}

            {result.final_response && (
              <div className="responseBox">
                <h3>Final Customer Response</h3>

                <p>
                  {result.final_response}
                </p>
              </div>
            )}

            <div className="thread">
              Thread ID: {result.thread_id}
            </div>

            <button
              className="secondaryButton"
              onClick={resetRequest}
            >
              New Request
            </button>
          </section>
        )}

        <footer>
          <p>
            FastAPI + LangGraph + LangChain +
            Next.js
          </p>
        </footer>
      </section>
    </main>
  );
}