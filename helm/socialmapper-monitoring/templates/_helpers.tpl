{{/*
Expand the name of the chart.
*/}}
{{- define "socialmapper-monitoring.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "socialmapper-monitoring.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "socialmapper-monitoring.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "socialmapper-monitoring.labels" -}}
helm.sh/chart: {{ include "socialmapper-monitoring.chart" . }}
{{ include "socialmapper-monitoring.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: monitoring
environment: {{ .Values.global.environment }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "socialmapper-monitoring.selectorLabels" -}}
app.kubernetes.io/name: {{ include "socialmapper-monitoring.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Prometheus selector labels
*/}}
{{- define "socialmapper-monitoring.prometheus.selectorLabels" -}}
app.kubernetes.io/name: prometheus
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: prometheus
{{- end }}

{{/*
Grafana selector labels
*/}}
{{- define "socialmapper-monitoring.grafana.selectorLabels" -}}
app.kubernetes.io/name: grafana
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: grafana
{{- end }}

{{/*
AlertManager selector labels
*/}}
{{- define "socialmapper-monitoring.alertmanager.selectorLabels" -}}
app.kubernetes.io/name: alertmanager
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: alertmanager
{{- end }}

{{/*
Create the name of the service account to use for Prometheus
*/}}
{{- define "socialmapper-monitoring.prometheus.serviceAccountName" -}}
{{- if .Values.prometheus.serviceAccount.create }}
{{- default (printf "%s-prometheus" (include "socialmapper-monitoring.fullname" .)) .Values.prometheus.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.prometheus.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use for kube-state-metrics
*/}}
{{- define "socialmapper-monitoring.kubeStateMetrics.serviceAccountName" -}}
{{- if .Values.kubeStateMetrics.serviceAccount.create }}
{{- default (printf "%s-kube-state-metrics" (include "socialmapper-monitoring.fullname" .)) .Values.kubeStateMetrics.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.kubeStateMetrics.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate certificates for webhook
*/}}
{{- define "socialmapper-monitoring.webhook.certs" -}}
{{- $ca := genCA "socialmapper-monitoring-ca" 365 }}
{{- $cert := genSignedCert "socialmapper-monitoring-webhook" nil (list "socialmapper-monitoring-webhook.monitoring.svc") 365 $ca }}
tls.crt: {{ $cert.Cert | b64enc }}
tls.key: {{ $cert.Key | b64enc }}
ca.crt: {{ $ca.Cert | b64enc }}
{{- end }}

{{/*
Common environment variables
*/}}
{{- define "socialmapper-monitoring.env" -}}
- name: CLUSTER_NAME
  value: {{ .Values.global.clusterName | quote }}
- name: ENVIRONMENT
  value: {{ .Values.global.environment | quote }}
- name: REGION
  value: {{ .Values.global.region | quote }}
- name: TZ
  value: {{ .Values.global.timezone | quote }}
{{- end }}

{{/*
Common resource requirements
*/}}
{{- define "socialmapper-monitoring.resources" -}}
{{- $resources := . }}
{{- if $.Values.development.enabled }}
{{- $multiplier := $.Values.costOptimization.resourceEfficiency.development.resourceMultiplier | default 0.5 }}
resources:
  requests:
    memory: {{ $resources.requests.memory | default "128Mi" }}
    cpu: {{ printf "%.0fm" (mul (regexFind "[0-9]+" ($resources.requests.cpu | default "100m") | float64) $multiplier) }}
  limits:
    memory: {{ $resources.limits.memory | default "256Mi" }}
    cpu: {{ printf "%.0fm" (mul (regexFind "[0-9]+" ($resources.limits.cpu | default "200m") | float64) $multiplier) }}
{{- else }}
{{- $multiplier := $.Values.costOptimization.resourceEfficiency.production.resourceMultiplier | default 1.0 }}
resources:
  requests:
    memory: {{ $resources.requests.memory | default "128Mi" }}
    cpu: {{ printf "%.0fm" (mul (regexFind "[0-9]+" ($resources.requests.cpu | default "100m") | float64) $multiplier) }}
  limits:
    memory: {{ $resources.limits.memory | default "256Mi" }}
    cpu: {{ printf "%.0fm" (mul (regexFind "[0-9]+" ($resources.limits.cpu | default "200m") | float64) $multiplier) }}
{{- end }}
{{- end }}

{{/*
Common security context
*/}}
{{- define "socialmapper-monitoring.securityContext" -}}
securityContext:
  runAsNonRoot: true
  runAsUser: 65534
  fsGroup: 65534
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
{{- end }}

{{/*
Common pod security context
*/}}
{{- define "socialmapper-monitoring.podSecurityContext" -}}
securityContext:
  runAsNonRoot: true
  runAsUser: 65534
  fsGroup: 65534
{{- end }}

{{/*
Common node selector and tolerations
*/}}
{{- define "socialmapper-monitoring.nodeSelector" -}}
{{- if .Values.costOptimization.spotInstances.enabled }}
nodeSelector:
  {{- toYaml .Values.costOptimization.spotInstances.nodeSelector | nindent 2 }}
tolerations:
  {{- toYaml .Values.costOptimization.spotInstances.tolerations | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Storage class name
*/}}
{{- define "socialmapper-monitoring.storageClassName" -}}
{{- .Values.global.storageClass | default "gp3" }}
{{- end }}

{{/*
Generate basic auth secret data
*/}}
{{- define "socialmapper-monitoring.basicAuth" -}}
{{- range $user, $password := .Values.auth.basic.users }}
{{ $user }}:{{ $password | htpasswd }}
{{- end }}
{{- end }}