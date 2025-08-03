import { Routes, Route } from 'react-router-dom'
import { HomePage } from '@/pages/HomePage'
import { GettingStartedPage } from '@/pages/GettingStartedPage'
import { TravelModesPage } from '@/pages/TravelModesPage'
import { ZCTAAnalysisPage } from '@/pages/ZCTAAnalysisPage'
import { AddressGeocodingPage } from '@/pages/AddressGeocodingPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { ComponentDemo } from '@/pages/ComponentDemo'
import { TestPage } from '@/pages/TestPage'
import { config } from '@/config'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/test" element={<TestPage />} />
      <Route path="/getting-started" element={<GettingStartedPage />} />
      <Route path="/travel-modes" element={<TravelModesPage />} />
      <Route path="/zcta-analysis" element={<ZCTAAnalysisPage />} />
      <Route path="/address-geocoding" element={<AddressGeocodingPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      {config.development.enableDevTools && (
        <Route path="/components" element={<ComponentDemo />} />
      )}
    </Routes>
  )
}