import { Link } from 'react-router-dom'
import { MapPin, Map, Route, BarChart3, Zap, Shield, ArrowRight, Github } from 'lucide-react'

export function HomePage() {
  const features = [
    {
      icon: MapPin,
      title: 'Location Analysis',
      description: 'Analyze accessibility from any location using various travel modes',
      link: '/getting-started',
      gradient: 'from-primary-400 to-primary-600'
    },
    {
      icon: Route,
      title: 'Travel Modes',
      description: 'Compare accessibility across walking, biking, driving, and transit',
      link: '/travel-modes',
      gradient: 'from-secondary-400 to-secondary-600'
    },
    {
      icon: Map,
      title: 'Address Geocoding',
      description: 'Convert addresses to coordinates for precise location analysis',
      link: '/address-geocoding',
      gradient: 'from-accent-400 to-accent-600'
    },
    {
      icon: BarChart3,
      title: 'Demographic Analysis',
      description: 'Integrate census data to understand community accessibility',
      link: '/zcta-analysis',
      gradient: 'from-primary-500 to-secondary-500'
    },
    {
      icon: Zap,
      title: 'High Performance',
      description: 'Optimized algorithms for fast isochrone generation',
      link: '/getting-started',
      gradient: 'from-accent-500 to-primary-500'
    },
    {
      icon: Shield,
      title: 'Open Source',
      description: 'Free and open source toolkit with active community support',
      link: '/getting-started',
      gradient: 'from-secondary-500 to-accent-500'
    }
  ]

  return (
    <div className="space-y-20">
      {/* Hero Section */}
      <section className="relative text-center py-20">
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-radial from-primary-500/10 via-transparent to-transparent" />
        </div>
        
        <h1 className="text-5xl sm:text-7xl font-display font-bold mb-6 animate-scale-in">
          <span className="gradient-text">SocialMapper</span>
        </h1>
        <p className="text-xl sm:text-2xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-12 animate-fade-in">
          A powerful Python toolkit for analyzing community accessibility by integrating 
          travel time analysis with demographic data
        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in">
          <Link
            to="/getting-started"
            className="group px-8 py-4 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold rounded-xl shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30 transform hover:-translate-y-0.5 transition-all duration-200"
          >
            Get Started
            <ArrowRight className="inline-block ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <a
            href="https://github.com/mihiarc/socialmapper"
            className="group px-8 py-4 glass glass-hover rounded-xl font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2"
          >
            <Github className="w-5 h-5" />
            View on GitHub
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </a>
        </div>
      </section>

      {/* Features Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature, index) => {
          const Icon = feature.icon
          return (
            <Link
              key={index}
              to={feature.link}
              className="group modern-card p-6 animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} p-2.5 mb-4 group-hover:scale-110 transition-transform`}>
                <Icon className="w-full h-full text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {feature.description}
              </p>
              <span className="inline-flex items-center text-sm font-medium gradient-text group-hover:gap-2 transition-all">
                Learn more
                <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
              </span>
            </Link>
          )
        })}
      </section>

      {/* Stats Section */}
      <section className="glass rounded-2xl p-8 text-center">
        <h2 className="text-2xl font-display font-semibold mb-8 gradient-text">
          Powerful Analytics at Your Fingertips
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          <div>
            <div className="text-4xl font-bold gradient-text mb-2">10K+</div>
            <div className="text-gray-600 dark:text-gray-400">POIs Analyzed</div>
          </div>
          <div>
            <div className="text-4xl font-bold gradient-text mb-2">50ms</div>
            <div className="text-gray-600 dark:text-gray-400">Avg. Query Time</div>
          </div>
          <div>
            <div className="text-4xl font-bold gradient-text mb-2">99.9%</div>
            <div className="text-gray-600 dark:text-gray-400">Accuracy</div>
          </div>
        </div>
      </section>
    </div>
  )
}