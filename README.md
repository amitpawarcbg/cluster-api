# cluster-api
Cluster API is a Kubernetes sub-project focused on providing declarative APIs and tooling to simplify provisioning, upgrading, and operating multiple Kubernetes clusters.
# What is Cluster API
 Started by the Kubernetes Special Interest Group (SIG) Cluster Lifecycle, the Cluster API project uses Kubernetes-style APIs and patterns to automate cluster lifecycle management for platform operators. The supporting infrastructure, like virtual machines, networks, load balancers, and VPCs, as well as the Kubernetes cluster configuration are all defined in the same way that application developers operate deploying and managing their workloads. This enables consistent and repeatable cluster deployments across a wide variety of infrastructure environments.
 
# Why do we need Cluster API?
Kubernetes is a complex system that relies on several components being configured correctly to have a working cluster. Recognizing this as a potential stumbling block for users, the community focused on simplifying the bootstrapping process. Today, over [100 Kubernetes distributions](https://www.cncf.io/certification/software-conformance/) and installers have been created, each with different default configurations for clusters and supported infrastructure providers. SIG Cluster Lifecycle saw a need for a single tool to address a set of common overlapping installation concerns and started kubeadm.

Kubeadm was designed as a focused tool for bootstrapping a best-practices Kubernetes cluster. The core tenet behind the kubeadm project was to create a tool that other installers can leverage and ultimately alleviate the amount of configuration that an individual installer needed to maintain. Since it began, kubeadm has become the underlying bootstrapping tool for several other applications, including Kubespray, Minikube, kind, etc.

However, while kubeadm and other bootstrap providers reduce installation complexity, they don’t address how to manage a cluster day-to-day or a Kubernetes environment long term. You are still faced with several questions when setting up a production environment, including:

1. How can I consistently provision machines, load balancers, VPC, etc., across multiple infrastructure providers and locations?
2. How can I automate cluster lifecycle management, including things like upgrades and cluster deletion?
3. How can I scale these processes to manage any number of clusters?
SIG Cluster Lifecycle began the Cluster API project as a way to address these gaps by building declarative, Kubernetes-style APIs, that automate cluster creation, configuration, and management. Using this model, Cluster API can also be extended to support any infrastructure provider (AWS, Azure, vSphere, etc.) or bootstrap provider (kubeadm is default) you need. See the growing list of available providers.

# Goals
* To manage the lifecycle (create, scale, upgrade, destroy) of Kubernetes-conformant clusters using a declarative API.
* To work in different environments, both on-premises and in the cloud.
* To define common operations, provide a default implementation, and provide the ability to swap out implementations for alternative ones.
* To reuse and integrate existing ecosystem components rather than duplicating their functionality (e.g. node-problem-detector, cluster autoscaler, SIG-Multi-cluster).
* To provide a transition path for Kubernetes lifecycle products to adopt Cluster API incrementally. Specifically, existing cluster lifecycle management tools should be able to adopt Cluster API in a staged manner, over the course of multiple releases, or even adopting a subset of Cluster API.

# Non-goals
* To add these APIs to Kubernetes core (kubernetes/kubernetes).
      * This API should live in a namespace outside the core and follow the best practices defined by api-reviewers, but is not subject to core-api constraints.
* To manage the lifecycle of infrastructure unrelated to the running of Kubernetes-conformant clusters.
* To force all Kubernetes lifecycle products (kops, kubespray, GKE, AKS, EKS, IKS etc.) to support or use these APIs.
* To manage non-Cluster API provisioned Kubernetes-conformant clusters.
* To manage a single cluster spanning multiple infrastructure providers.
* To configure a machine at any time other than create or upgrade.
* To duplicate functionality that exists or is coming to other tooling, e.g., updating kubelet configuration (c.f. dynamic kubelet configuration), or updating apiserver, controller-manager, scheduler configuration (c.f. component-config effort) after the cluster is deployed.
 
# Concepts

![image](https://user-images.githubusercontent.com/88305831/170925138-b5bf0ea9-a2ad-4896-8c02-854fb5b6ea32.png)

## Management cluster
A Kubernetes cluster that manages the lifecycle of Workload Clusters. A Management Cluster is also where one or more Infrastructure Providers run, and where resources such as Machines are stored.

## Workload cluster
A Kubernetes cluster whose lifecycle is managed by a Management Cluster.

## Infrastructure provider
A source of computational resources, such as compute and networking. For example, cloud Infrastructure Providers include AWS, Azure, and Google, and bare metal Infrastructure Providers include VMware, MAAS, and metal3.io.

When there is more than one way to obtain resources from the same Infrastructure Provider (such as AWS offering both EC2 and EKS), each way is referred to as a variant.

## Bootstrap provider
The Bootstrap Provider is responsible for:

1. Generating the cluster certificates, if not otherwise specified
2. Initializing the control plane, and gating the creation of other nodes until it is complete
3. Joining control plane and worker nodes to the cluster

## Control plane
The control plane is a set of components that serve the Kubernetes API and continuously reconcile desired state using control loops.

1. Machine-based control planes are the most common type. Dedicated machines are provisioned, running static pods for components such as kube-apiserver, kube-controller-manager and kube-scheduler.

2. Pod-based deployments require an external hosting cluster. The control plane components are deployed using standard Deployment and StatefulSet objects and the API is exposed using a Service.

3. External control planes are offered and controlled by some system other than Cluster API, such as GKE, AKS, EKS, or IKS.

The default provider uses kubeadm to bootstrap the control plane. As of v1alpha3, it exposes the configuration via the KubeadmControlPlane object. The controller, capi-kubeadm-control-plane-controller-manager, can then create Machine and BootstrapConfig objects based on the requested replicas in the KubeadmControlPlane object.

## Custom Resource Definitions (CRDs)
A CustomResourceDefinition is a built-in resource that lets you extend the Kubernetes API. Each CustomResourceDefinition represents a customization of a Kubernetes installation. The Cluster API provides and relies on several CustomResourceDefinitions:

  ## Machine
  A “Machine” is the declarative spec for an infrastructure component hosting a Kubernetes Node (for example, a VM). If a new Machine object is created, a provider-specific controller will provision and install a new host to register as a new Node matching the Machine spec. If the Machine’s spec is updated, the controller replaces the host with a new one matching the updated spec. If a Machine object is deleted, its underlying infrastructure and corresponding Node will be deleted by the controller.

  Common fields such as Kubernetes version are modeled as fields on the Machine’s spec. Any information that is provider-specific is part of the InfrastructureRef and is not portable between different providers.

  ## Machine Immutability (In-place Upgrade vs. Replace)
  From the perspective of Cluster API, all Machines are immutable: once they are created, they are never updated (except for labels, annotations and status), only deleted.

  For this reason, MachineDeployments are preferable. MachineDeployments handle changes to machines by replacing them, in the same way core Deployments handle changes to Pod specifications.

  ## MachineDeployment
  A MachineDeployment provides declarative updates for Machines and MachineSets.

  A MachineDeployment works similarly to a core Kubernetes Deployment. A MachineDeployment reconciles changes to a Machine spec by rolling out changes to 2 MachineSets, the old and the newly updated.

  ## MachineSet
  A MachineSet’s purpose is to maintain a stable set of Machines running at any given time.

  A MachineSet works similarly to a core Kubernetes ReplicaSet. MachineSets are not meant to be used directly, but are the mechanism MachineDeployments use to reconcile desired state.

  ## MachineHealthCheck
  A MachineHealthCheck defines the conditions when a Node should be considered unhealthy.

  If the Node matches these unhealthy conditions for a given user-configured time, the MachineHealthCheck initiates remediation of the Node. Remediation of Nodes is performed by deleting the corresponding Machine.

  MachineHealthChecks will only remediate Nodes if they are owned by a MachineSet. This ensures that the Kubernetes cluster does not lose capacity, since the MachineSet will create a new Machine to replace the failed Machine.

  ## BootstrapData
  BootstrapData contains the Machine or Node role-specific initialization data (usually cloud-init) used by the Infrastructure Provider to bootstrap a Machine into a Node.

## In this article we will see how we can use CLuster API to automate cluster lifecycle management for AWS/Azure/GCP infrastructure providers.

Cluster lifecycle management does installing and managing the cluster lifecycle. It handles deployment, upgrade, migration and deletion of cluster resources.

So let's start with prerequisite for installting Cluster-API

# Common Prerequisites
1. Install and setup [kubectl](https://kubernetes.io/docs/tasks/tools/) in your local environment.
2. Install [minikube](https://minikube.sigs.k8s.io/docs/start/) or [kind](https://kind.sigs.k8s.io/docs/user/quick-start/).

## Install and/or configure a Kubernetes cluster
Cluster API requires an existing Kubernetes cluster accessible via kubectl. 
During the installation process the Kubernetes cluster will be transformed into a management cluster by installing the Cluster API provider components, so it is recommended to keep it separated from any application workload.

It is a common practice to create a temporary, local bootstrap cluster which is then used to provision a target management cluster on the selected infrastructure provider.

In this article we will be using minikube configured on our local linux VM/machine which will serve as a management cluster.

## Install clusterctl
By this step we should have kubectl and minikube/kind k8s cluster setup and ready to use.

The clusterctl CLI tool handles the lifecycle of a Cluster API management cluster.
clusterctl CLI tool support instllation on Linux and Mac OS.
We will be using Linux distribution for clusterctl CLI tool.

**Install clusterctl binary with curl on linux**

Download the latest release; on linux, type:

* "curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.1.3/clusterctl-linux-amd64 -o clusterctl"

Make the clusterctl binary executable.

* "chmod +x ./clusterctl"

Move the binary in to your PATH.

* "sudo mv ./clusterctl /usr/local/bin/clusterctl"

Test to ensure the version you installed is up-to-date:

* "clusterctl version"

## Initialize the management cluster
Now that we’ve got clusterctl installed and all the prerequisites in place, let’s transform the Kubernetes cluster into a management cluster by using **"clusterctl init"**.

The command accepts as input a list of providers to install; when executed for the first time, 
**"clusterctl init"** automatically adds to the list the **cluster-api** core provider, and if unspecified, it also adds the **kubeadm bootstrap** and **kubeadm control-plane providers**.


## Now at this point we have setup the Cluster API cli too "clusterctl". So lets enable the bash autocompletion feature for it.

* Source the completion script in your ~/.bash_profile file:

    "source <(clusterctl completion bash)"

* Add the completion script to the /usr/local/etc/bash_completion.d directory:

    "clusterctl completion bash >/usr/local/etc/bash_completion.d/clusterctl"

**Note**:- If the directory "/usr/local/etc/bash_completion.d" is not present on server then you can create it.

## In this section we will configure infrastructre provide AWS and later deploy kubernetes cluster on it.

**Initialize AWS provider.**

Download the latest binary of **clusterawsadm** from the [AWS provider releases](https://github.com/kubernetes-sigs/cluster-api-provider-aws/releases) and make sure to place it in your path.

The [clusterawsadm](https://cluster-api-aws.sigs.k8s.io/clusterawsadm/clusterawsadm.html) command line utility assists with identity and access management (IAM) for [Cluster API Provider AWS](https://cluster-api-aws.sigs.k8s.io/).

* export AWS_REGION=us-east-1 # This is used to help encode your environment variables

* export AWS_ACCESS_KEY_ID=<your-access-key>
 
* export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
 
* export AWS_SESSION_TOKEN=<session-token> # If you are using Multi-Factor Auth.

The clusterawsadm utility takes the credentials that you set as environment
variables and uses them to create a CloudFormation stack in your AWS account
with the correct IAM resources.
 
* "clusterawsadm bootstrap iam create-cloudformation-stack"

Create the base64 encoded credentials using clusterawsadm.
This command uses your environment variables and encodes
them in a value to be stored in a Kubernetes Secret.
 
* "export AWS_B64ENCODED_CREDENTIALS=$(clusterawsadm bootstrap credentials encode-as-profile)"

Finally, initialize the management cluster
 
* "clusterctl init --infrastructure aws"


