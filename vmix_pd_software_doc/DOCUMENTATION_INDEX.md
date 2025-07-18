# Documentation Index - PD Integrated Software

## 📚 Documentation Overview

This documentation set covers the PD Integrated Software project, which combines NDI preview, vMix tally, and SRT streaming capabilities into a unified application for broadcast production.

## 🗂️ Documentation Structure

### 1. Project Overview
- **[README.md](README.md)** - Start here for project introduction and navigation
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Current project status, architecture, and roadmap

### 2. Technical Guides

#### NDI Implementation
- **[NDI_TECHNICAL_GUIDE.md](NDI_TECHNICAL_GUIDE.md)** - Comprehensive NDI implementation reference
  - NDI technology overview
  - Python library comparison (ndi-python vs cyndilib)
  - 59.94fps implementation details
  - 16:9 aspect ratio handling
  - Performance optimization techniques
  - Code examples and best practices

#### vMix Integration
- **[vMix_TALLY_TECHNICAL_GUIDE.md](vMix_TALLY_TECHNICAL_GUIDE.md)** - Complete vMix tally system documentation
  - Communication methods (TCP/HTTP/WebSocket)
  - Hybrid implementation architecture
  - WebSocket relay server design
  - Real-time synchronization
  - Error handling and recovery
  - Performance considerations

### 3. Problem Solving
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Consolidated troubleshooting guide
  - Quick diagnosis checklist
  - Common issues and solutions
  - Platform-specific problems
  - Performance optimization
  - Emergency recovery procedures
  - Debugging techniques

### 4. Legacy Documentation

These documents contain historical information that has been consolidated into the guides above:

- `PD 비디오 프리뷰 및 탈리 시스템 - 완전한 기술 문서.md` - Original comprehensive technical document (102KB)
- `NDI 소프트웨어 GUI 프리뷰 16_9 고정 및 59.94fps 프레임레이트 유지 완전 구현 가이드.md` - Frame rate implementation details
- `NDI 프레임 레이트 최적화 해결방법 및 기법.md` - Frame rate optimization techniques
- `NDI-Python 프레임레이트 동기화 문제 분석.md` - Frame synchronization analysis
- `NDI_프리뷰_문제_해결_보고서.md` - Preview issue resolution report
- `ndi_gui_프레임드랍문제해결방안.md` - Frame drop solutions
- `ndi_test소프트웨어.md` - NDI test software documentation

## 📖 Reading Order

### For New Developers
1. Start with [README.md](README.md)
2. Review [PROJECT_PLAN.md](PROJECT_PLAN.md) for architecture
3. Study [NDI_TECHNICAL_GUIDE.md](NDI_TECHNICAL_GUIDE.md) for video implementation
4. Read [vMix_TALLY_TECHNICAL_GUIDE.md](vMix_TALLY_TECHNICAL_GUIDE.md) for tally system
5. Keep [TROUBLESHOOTING.md](TROUBLESHOOTING.md) handy for issues

### For Troubleshooting
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
2. Refer to specific technical guides for deep dives
3. Review legacy documents for historical context if needed

### For System Administrators
1. [PROJECT_PLAN.md](PROJECT_PLAN.md) - Deployment information
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common operational issues
3. Technical guides for specific component configuration

## 🔍 Quick Reference

### NDI Topics
- **Frame Rate (59.94fps)**: [NDI_TECHNICAL_GUIDE.md#frame-rate-implementation](NDI_TECHNICAL_GUIDE.md#frame-rate-implementation)
- **Aspect Ratio (16:9)**: [NDI_TECHNICAL_GUIDE.md#aspect-ratio-implementation](NDI_TECHNICAL_GUIDE.md#aspect-ratio-implementation)
- **Library Selection**: [NDI_TECHNICAL_GUIDE.md#python-ndi-libraries-comparison](NDI_TECHNICAL_GUIDE.md#python-ndi-libraries-comparison)
- **Performance**: [NDI_TECHNICAL_GUIDE.md#performance-optimization](NDI_TECHNICAL_GUIDE.md#performance-optimization)

### vMix Topics
- **Connection Methods**: [vMix_TALLY_TECHNICAL_GUIDE.md#communication-methods](vMix_TALLY_TECHNICAL_GUIDE.md#communication-methods)
- **WebSocket Relay**: [vMix_TALLY_TECHNICAL_GUIDE.md#websocket-relay-architecture](vMix_TALLY_TECHNICAL_GUIDE.md#websocket-relay-architecture)
- **Error Recovery**: [vMix_TALLY_TECHNICAL_GUIDE.md#error-handling](vMix_TALLY_TECHNICAL_GUIDE.md#error-handling)

### Common Issues
- **No NDI Sources**: [TROUBLESHOOTING.md#no-ndi-sources-found](TROUBLESHOOTING.md#no-ndi-sources-found)
- **GUI Freezing**: [TROUBLESHOOTING.md#gui-freezing-issues](TROUBLESHOOTING.md#gui-freezing-issues)
- **Frame Rate Problems**: [TROUBLESHOOTING.md#frame-rate-issues-not-achieving-5994fps](TROUBLESHOOTING.md#frame-rate-issues-not-achieving-5994fps)
- **vMix Connection**: [TROUBLESHOOTING.md#cannot-connect-to-vmix](TROUBLESHOOTING.md#cannot-connect-to-vmix)

## 📝 Documentation Standards

### File Naming
- Technical guides: `COMPONENT_TECHNICAL_GUIDE.md`
- Troubleshooting: `TROUBLESHOOTING.md`
- Project overview: `PROJECT_PLAN.md`

### Content Structure
1. Table of Contents for documents > 500 lines
2. Clear section headers with markdown hierarchy
3. Code examples with syntax highlighting
4. Visual diagrams where applicable
5. Cross-references between documents

### Language
- Technical content in English
- User-facing content may include Korean (한국어)
- Code comments in English
- Error messages bilingual where appropriate

## 🔄 Version History

- **v1.0.0** (2025-01-09) - Initial consolidated documentation
- **v0.9.0** - Legacy individual documents
- **v0.8.0** - Original technical specifications

## 📞 Documentation Feedback

For documentation improvements or corrections:
1. Create an issue on GitHub
2. Tag with `documentation`
3. Reference the specific document and section

---

*Last Updated: 2025-01-14*
*Maintained by: PD Software Team*