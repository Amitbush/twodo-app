# 📱 Twodo App - Backend & Frontend

Core application repository containing the source code and deployment manifests.

## 🛠️ Technology Stack
- **Backend**: Python-based API connected to PostgreSQL.
- **Containerization**: Docker.
- **Orchestration**: Helm Chart (located in `twodo-chart/`).

## 📂 Repository Structure
- `app/` - Application source code.
- `twodo-chart/` - Production Helm Chart including Templates, Values, and Ingress rules.
- `Dockerfile` - Container build instructions.

## 🚢 CI/CD Workflow
The application is deployed using a GitOps pattern via **ArgoCD**. Any changes to the `twodo-chart/` directory are automatically synchronized and deployed to the EKS cluster.

## ☸️ Helm Commands
To lint the chart for errors:
```bash
helm lint ./twodo-chart