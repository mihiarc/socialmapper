import { useState } from 'react'
import { 
  Select, SelectEnhanced, TravelModeSelect, MultiSelect,
  Input, Button, TextArea, Checkbox, RadioGroup,
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
  Spinner
} from '@/components'
import { TravelMode } from '@/types'
import { Search, Mail, Lock, Plus, Save, Trash2, Download, Settings, ChevronRight } from 'lucide-react'

export function ComponentDemo() {
  // Select states
  const [basicSelect, setBasicSelect] = useState('')
  const [enhancedSelect, setEnhancedSelect] = useState('')
  const [travelMode, setTravelMode] = useState<TravelMode>(TravelMode.Walk)
  const [multiSelect, setMultiSelect] = useState<string[]>([])
  
  // Input states
  const [textInput, setTextInput] = useState('')
  const [emailInput, setEmailInput] = useState('')
  const [passwordInput, setPasswordInput] = useState('')
  const [searchInput, setSearchInput] = useState('')
  
  // Other form states
  const [textAreaValue, setTextAreaValue] = useState('')
  const [checkboxValue, setCheckboxValue] = useState(false)
  const [radioValue, setRadioValue] = useState('option1')
  const [loading, setLoading] = useState(false)
  
  const basicOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
  ]
  
  const poiOptions = [
    { value: 'amenity:pharmacy', label: 'Pharmacy', description: 'Pharmacies and drugstores' },
    { value: 'amenity:hospital', label: 'Hospital', description: 'Medical centers and hospitals' },
    { value: 'amenity:clinic', label: 'Clinic', description: 'Medical clinics and health centers' },
    { value: 'amenity:doctors', label: 'Doctor', description: 'Doctor offices' },
    { value: 'shop:supermarket', label: 'Supermarket', description: 'Grocery stores and supermarkets' },
    { value: 'amenity:library', label: 'Library', description: 'Public libraries' },
    { value: 'amenity:school', label: 'School', description: 'Educational institutions' },
  ]
  
  const radioOptions = [
    { value: 'option1', label: 'First Option', description: 'This is the first option' },
    { value: 'option2', label: 'Second Option', description: 'This is the second option' },
    { value: 'option3', label: 'Third Option', description: 'This is the third option' },
  ]

  const handleDemoAction = () => {
    setLoading(true)
    setTimeout(() => setLoading(false), 2000)
  }

  return (
    <div className="px-4 py-6 sm:px-0 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Component Showcase</h1>
      
      <div className="space-y-8">
        {/* Input Components */}
        <Card variant="default">
          <CardHeader>
            <CardTitle>Input Components</CardTitle>
            <CardDescription>Enhanced input fields with variants, sizes, and icons</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Input
                  label="Default Input"
                  placeholder="Enter text..."
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                />
                
                <Input
                  label="Search Input"
                  placeholder="Search..."
                  iconType="search"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                />
                
                <Input
                  label="Email Input"
                  type="email"
                  placeholder="you@example.com"
                  iconType="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                />
                
                <Input
                  label="Password Input"
                  type="password"
                  placeholder="Enter password"
                  iconType="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                />
              </div>
              
              <div className="space-y-4">
                <Input
                  label="With Error State"
                  placeholder="Enter value..."
                  error="This field is required"
                />
                
                <Input
                  label="Filled Variant"
                  placeholder="Filled input..."
                  variant="filled"
                />
                
                <Input
                  label="Ghost Variant"
                  placeholder="Ghost input..."
                  variant="ghost"
                />
                
                <div className="grid grid-cols-3 gap-2">
                  <Input placeholder="Small" size="sm" />
                  <Input placeholder="Medium" size="md" />
                  <Input placeholder="Large" size="lg" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Button Components */}
        <Card variant="default">
          <CardHeader>
            <CardTitle>Button Components</CardTitle>
            <CardDescription>Enhanced buttons with loading states, icons, and variants</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Button Variants */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Variants</h4>
                <div className="flex flex-wrap gap-3">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="danger">Danger</Button>
                  <Button variant="success">Success</Button>
                </div>
              </div>

              {/* Button Sizes */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Sizes</h4>
                <div className="flex items-center gap-3">
                  <Button size="xs">Extra Small</Button>
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                  <Button size="xl">Extra Large</Button>
                </div>
              </div>

              {/* Buttons with Icons */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">With Icons</h4>
                <div className="flex flex-wrap gap-3">
                  <Button leftIcon={<Plus />}>Add Item</Button>
                  <Button rightIcon={<ChevronRight />}>Continue</Button>
                  <Button leftIcon={<Save />} variant="success">Save Changes</Button>
                  <Button leftIcon={<Trash2 />} variant="danger">Delete</Button>
                  <Button loading={loading} onClick={handleDemoAction}>
                    {loading ? 'Processing...' : 'Click to Load'}
                  </Button>
                </div>
              </div>

              {/* Full Width Buttons */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Full Width</h4>
                <div className="space-y-2 max-w-sm">
                  <Button fullWidth leftIcon={<Download />}>Download Report</Button>
                  <Button fullWidth variant="outline" rightIcon={<Settings />}>
                    Settings
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* TextArea Component */}
        <Card variant="default">
          <CardHeader>
            <CardTitle>TextArea Component</CardTitle>
            <CardDescription>Enhanced textarea with character count and resize options</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <TextArea
                label="Default TextArea"
                placeholder="Enter your message..."
                value={textAreaValue}
                onChange={(e) => setTextAreaValue(e.target.value)}
                showCharCount
                maxLength={200}
              />
              
              <TextArea
                label="Filled Variant - No Resize"
                placeholder="This textarea cannot be resized..."
                variant="filled"
                resize="none"
              />
            </div>
          </CardContent>
        </Card>

        {/* Checkbox & Radio Components */}
        <Card variant="default">
          <CardHeader>
            <CardTitle>Checkbox & Radio Components</CardTitle>
            <CardDescription>Enhanced selection controls with descriptions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h4 className="font-medium">Checkboxes</h4>
                <Checkbox
                  label="Accept terms and conditions"
                  description="You agree to our Terms of Service and Privacy Policy"
                  checked={checkboxValue}
                  onChange={(e) => setCheckboxValue(e.target.checked)}
                />
                
                <Checkbox
                  label="Subscribe to newsletter"
                  checked
                  disabled
                />
                
                <div className="flex gap-4">
                  <Checkbox label="Small" size="sm" />
                  <Checkbox label="Medium" size="md" />
                  <Checkbox label="Large" size="lg" />
                </div>
              </div>
              
              <div>
                <RadioGroup
                  name="demo-radio"
                  label="Select an option"
                  value={radioValue}
                  onChange={setRadioValue}
                  options={radioOptions}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Select Components (existing) */}
        <Card variant="default">
          <CardHeader>
            <CardTitle>Standard Select Component</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-w-md space-y-4">
              <Select
                label="Choose an option"
                placeholder="Select an option..."
                options={basicOptions}
                value={basicSelect}
                onChange={(e) => setBasicSelect(e.target.value)}
              />
              
              <Select
                label="With Error State"
                placeholder="Select an option..."
                options={basicOptions}
                value=""
                onChange={(e) => setBasicSelect(e.target.value)}
                error="This field is required"
              />
              
              <Select
                label="Disabled State"
                placeholder="Select an option..."
                options={basicOptions}
                value="option1"
                disabled
                onChange={(e) => setBasicSelect(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Enhanced Select (existing) */}
        <Card variant="default">
          <CardHeader>
            <CardTitle>Enhanced Select Component</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-w-md space-y-4">
              <SelectEnhanced
                label="Default Variant"
                placeholder="Select an option..."
                options={basicOptions}
                value={enhancedSelect}
                onChange={(e) => setEnhancedSelect(e.target.value)}
              />
              
              <SelectEnhanced
                label="Filled Variant"
                placeholder="Select an option..."
                options={basicOptions}
                value={enhancedSelect}
                variant="filled"
                onChange={(e) => setEnhancedSelect(e.target.value)}
              />
              
              <SelectEnhanced
                label="Ghost Variant"
                placeholder="Select an option..."
                options={basicOptions}
                value={enhancedSelect}
                variant="ghost"
                onChange={(e) => setEnhancedSelect(e.target.value)}
              />
              
              <div className="grid grid-cols-3 gap-4">
                <SelectEnhanced
                  label="Small Size"
                  options={basicOptions}
                  size="sm"
                  value={enhancedSelect}
                  onChange={(e) => setEnhancedSelect(e.target.value)}
                />
                
                <SelectEnhanced
                  label="Medium Size"
                  options={basicOptions}
                  size="md"
                  value={enhancedSelect}
                  onChange={(e) => setEnhancedSelect(e.target.value)}
                />
                
                <SelectEnhanced
                  label="Large Size"
                  options={basicOptions}
                  size="lg"
                  value={enhancedSelect}
                  onChange={(e) => setEnhancedSelect(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Multi Select (existing) */}
        <Card variant="default">
          <CardHeader>
            <CardTitle>Multi-Select Component</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-w-md space-y-4">
              <MultiSelect
                label="Select Points of Interest"
                placeholder="Choose POI types..."
                options={poiOptions}
                value={multiSelect}
                onChange={setMultiSelect}
              />
              
              {multiSelect.length > 0 && (
                <div className="p-4 bg-gray-50 rounded-md">
                  <p className="text-sm font-medium text-gray-700 mb-2">Selected values:</p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {multiSelect.map(value => (
                      <li key={value}>• {value}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Card Variants */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Card Variants</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card variant="default">
              <CardHeader>
                <CardTitle size="md">Default Card</CardTitle>
              </CardHeader>
              <CardContent>
                This is the default card style with subtle border and shadow.
              </CardContent>
            </Card>

            <Card variant="bordered">
              <CardHeader>
                <CardTitle size="md">Bordered Card</CardTitle>
              </CardHeader>
              <CardContent>
                This card has a more prominent border.
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardHeader>
                <CardTitle size="md">Elevated Card</CardTitle>
              </CardHeader>
              <CardContent>
                This card has a stronger shadow for elevation.
              </CardContent>
            </Card>

            <Card variant="ghost">
              <CardHeader>
                <CardTitle size="md">Ghost Card</CardTitle>
              </CardHeader>
              <CardContent>
                This card has a subtle background.
              </CardContent>
            </Card>

            <Card variant="gradient">
              <CardHeader>
                <CardTitle size="md">Gradient Card</CardTitle>
              </CardHeader>
              <CardContent>
                This card has a gradient background.
              </CardContent>
            </Card>

            <Card variant="default" hover>
              <CardHeader>
                <CardTitle size="md">Hoverable Card</CardTitle>
              </CardHeader>
              <CardContent>
                This card scales and changes on hover.
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}