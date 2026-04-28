# Akamai AMD Deployment with Pulumi

This repository contains a **Pulumi** project written in **Python** to deploy a barebones **Akamai Adaptive Media Delivery (AMD)** configuration. 

It is specifically optimized for use with **Shared Certificates** (`*.akamaized.net`) and handles the mandatory "Product Behaviors" required by the Akamai Property Manager API (PAPI).

## 🚀 Overview

The project automates the creation of:
* **CP Code**: For billing and reporting.
* **Edge Hostname**: A shared certificate hostname on the Akamai network.
* **Property**: An AMD configuration with a specific rule tree.
* **Activation**: Automated deployment to the Akamai **Staging** network.

## 📋 Prerequisites

Before running this project, ensure you have the following:

1.  **Akamai API Access**: An `.edgerc` file with valid credentials for the Property Manager API (PAPI).
2.  **Pulumi CLI**: Installed and authenticated.
3.  **Python 3.9+**: Installed on your local machine.
4.  **Akamai Contract Details**: Your `contractId` and `groupId`.

## 🛠️ Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd akamai-pulumi-amd
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install pulumi pulumi_akamai
    ```

3.  **Configure your stack:**
    You must set the following configuration variables for the project to work:

    ```bash
    pulumi config set contractId "ctr_XXXXXX"
    pulumi config set groupId "grp_XXXXXX"
    pulumi config set productId "prd_Adaptive_Media_Delivery"
    pulumi config set propertyName "my-amd-config"
    pulumi config set originHostname "origin.example.com"
    pulumi config set edgeHostname "example.akamaized.net"
    pulumi config set propertyHostname "video.example.com"
    pulumi config set activateNetwork "STAGING"
    pulumi config set --path 'notificationEmails[0]' "admin@example.com"
    ```

## 🏗️ Project Logic

### Mandatory AMD Behaviors
The script automatically includes the following behaviors in the **Default Rule**, which are required by Akamai to activate an AMD property:
* **Origin Characteristics**: Optimized for your origin location.
* **Client Characteristics**: Optimized for your target audience region.
* **Segmented Media Optimization**: Configured for `ON_DEMAND` delivery.

### Shared Certificate Handling
Because this project uses `akamaized.net`, it includes specific settings to avoid common API validation errors:
* **`cert_provisioning_type`**: Set to `CPS_MANAGED`.
* **`is_secure`**: Set to `False` (Standard TLS mode).

## 🚢 Deployment

To preview the changes:
```bash
pulumi preview
```

To deploy the infrastructure to Akamai:
```bash
pulumi up
```

*Note: New Edge Hostnames can take **10-15 minutes** to propagate. Do not interrupt the process.*

## 🔍 Verification

Once the activation is complete, you can test the deployment using Akamai Pragma headers:

```bash
curl -I -L -H "Pragma: akamai-x-cache-on, akamai-x-get-cache-key" https://<your-edge-hostname>
```

Look for `X-Cache: TCP_HIT` to confirm the content is being served from the Akamai Edge.

***

