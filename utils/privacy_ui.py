"""Privacy and Data Management UI for FundPortal"""

import streamlit as st
import json
from datetime import datetime
from utils.gdpr_compliance import GDPRComplianceManager
from utils.privacy_documents import (
    get_privacy_policy,
    get_terms_of_service,
    get_marketing_consent_text,
    get_analytics_consent_text
)


def show_consent_dialog(user_id: int, consent_type: str = 'all') -> bool:
    """Show consent dialog for new users or policy updates

    Args:
        user_id: User ID
        consent_type: Type of consent ('all', 'privacy_policy', 'terms', 'marketing', 'analytics')

    Returns:
        True if all required consents granted
    """
    gdpr = GDPRComplianceManager()

    st.markdown("## 🔒 Gizlilik ve Veri Koruma")

    if consent_type in ['all', 'privacy_policy']:
        st.markdown("### 📋 Gizlilik Politikası ve KVKK Aydınlatma Metni")

        with st.expander("📄 Gizlilik Politikasını Oku (KVKK/GDPR)", expanded=False):
            st.markdown(get_privacy_policy('tr'))

        privacy_consent = st.checkbox(
            "✅ Gizlilik Politikasını ve KVKK Aydınlatma Metnini okudum, anladım ve kabul ediyorum. (Zorunlu)",
            key=f"privacy_consent_{user_id}"
        )

    if consent_type in ['all', 'terms']:
        st.markdown("### 📜 Kullanım Koşulları")

        with st.expander("📄 Kullanım Koşullarını Oku", expanded=False):
            st.markdown(get_terms_of_service())

        terms_consent = st.checkbox(
            "✅ Kullanım Koşullarını okudum ve kabul ediyorum. (Zorunlu)",
            key=f"terms_consent_{user_id}"
        )

    st.markdown("---")
    st.markdown("### ⚙️ Opsiyonel İzinler")
    st.markdown("*Aşağıdaki izinler opsiyoneldir ve platformu kullanmak için gerekli değildir.*")

    if consent_type in ['all', 'marketing']:
        with st.expander("📧 Pazarlama İletişimi Detayları"):
            st.markdown(get_marketing_consent_text())

        marketing_consent = st.checkbox(
            "📧 Pazarlama ve bilgilendirme e-postaları almak istiyorum. (Opsiyonel)",
            key=f"marketing_consent_{user_id}"
        )
    else:
        marketing_consent = False

    if consent_type in ['all', 'analytics']:
        with st.expander("📊 Analitik Veriler Detayları"):
            st.markdown(get_analytics_consent_text())

        analytics_consent = st.checkbox(
            "📊 Platform iyileştirme için kullanım verilerimin toplanmasına izin veriyorum. (Opsiyonel)",
            key=f"analytics_consent_{user_id}"
        )
    else:
        analytics_consent = False

    st.markdown("---")

    # Privacy information
    with st.expander("ℹ️ Haklarınız Hakkında"):
        st.markdown("""
        **KVKK ve GDPR kapsamında sahip olduğunuz haklar:**

        ✅ **Bilgi Talep Etme:** Hangi verilerinizin işlendiğini öğrenme
        ✅ **Düzeltme:** Yanlış verileri düzeltme
        ✅ **Silme (Unutulma Hakkı):** Verilerinizin silinmesini talep etme
        ✅ **Veri Taşınabilirliği:** Verilerinizi JSON formatında alma
        ✅ **İtiraz Etme:** Veri işlemeye itiraz etme

        Bu haklara platform üzerinden "Ayarlar > Gizlilik ve Veri Yönetimi" bölümünden erişebilirsiniz.
        """)

    st.markdown("---")

    # Consent button
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("✅ Onaylıyorum ve Devam Et", type="primary", use_container_width=True):
            # Check required consents
            required_ok = True

            if consent_type in ['all', 'privacy_policy']:
                if not privacy_consent:
                    st.error("⚠️ Gizlilik Politikası onayı zorunludur.")
                    required_ok = False

            if consent_type in ['all', 'terms']:
                if not terms_consent:
                    st.error("⚠️ Kullanım Koşulları onayı zorunludur.")
                    required_ok = False

            if required_ok:
                # Record consents
                version = "1.0"

                if consent_type in ['all', 'privacy_policy']:
                    gdpr.record_consent(user_id, 'privacy_policy', version, True)

                if consent_type in ['all', 'terms']:
                    gdpr.record_consent(user_id, 'terms_of_service', version, True)

                if consent_type in ['all', 'marketing']:
                    gdpr.record_consent(user_id, 'marketing', version, marketing_consent)

                if consent_type in ['all', 'analytics']:
                    gdpr.record_consent(user_id, 'analytics', version, analytics_consent)

                st.success("✅ Onayınız kaydedildi!")
                return True

    return False


def display_privacy_settings(user_id: int):
    """Display privacy and data management settings page

    Args:
        user_id: User ID
    """
    gdpr = GDPRComplianceManager()

    st.header("🔒 Gizlilik ve Veri Yönetimi")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚙️ İzinler",
        "📊 Verilerim",
        "📥 Veri İndir",
        "🗑️ Hesabı Sil",
        "📜 Audit Trail"
    ])

    with tab1:
        st.subheader("⚙️ İzin Yönetimi")

        # Get current consents
        consents = gdpr.get_user_consents(user_id)

        st.markdown("### Zorunlu İzinler")
        st.info("Bu izinler platformu kullanabilmek için gereklidir ve değiştirilemez.")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Gizlilik Politikası", "✅ Onaylı" if consents.get('privacy_policy', False) else "❌ Onaylı Değil")
        with col2:
            st.metric("Kullanım Koşulları", "✅ Onaylı" if consents.get('terms_of_service', False) else "❌ Onaylı Değil")

        st.markdown("---")
        st.markdown("### Opsiyonel İzinler")

        # Marketing consent
        marketing_current = consents.get('marketing', False)
        marketing_new = st.checkbox(
            "📧 Pazarlama ve bilgilendirme e-postaları",
            value=marketing_current,
            key="marketing_update"
        )

        if marketing_new != marketing_current:
            if st.button("💾 Pazarlama İzni Güncelle", key="update_marketing"):
                gdpr.record_consent(user_id, 'marketing', '1.0', marketing_new)
                st.success("✅ Pazarlama izniniz güncellendi!")
                st.rerun()

        # Analytics consent
        analytics_current = consents.get('analytics', False)
        analytics_new = st.checkbox(
            "📊 Kullanım verilerinin toplanması (Platform iyileştirme)",
            value=analytics_current,
            key="analytics_update"
        )

        if analytics_new != analytics_current:
            if st.button("💾 Analitik İzni Güncelle", key="update_analytics"):
                gdpr.record_consent(user_id, 'analytics', '1.0', analytics_new)
                st.success("✅ Analitik izniniz güncellendi!")
                st.rerun()

        st.markdown("---")

        with st.expander("📋 İzin Geçmişi"):
            consent_history = gdpr.get_consent_audit_trail(user_id)
            if consent_history:
                for record in consent_history[:10]:  # Last 10
                    status = "✅ Verildi" if record['is_granted'] else "❌ Geri Çekildi"
                    date = record.get('granted_at') or record.get('withdrawn_at', 'N/A')
                    st.text(f"{record['consent_type']}: {status} - {date}")
            else:
                st.info("Henüz izin kaydı yok.")

    with tab2:
        st.subheader("📊 Saklanan Verilerim")

        st.markdown("""
        Platform üzerinde saklanan kişisel verileriniz:

        **Kimlik Bilgileri:**
        - Kullanıcı adı
        - E-posta adresi
        - Kayıt tarihi ve son giriş zamanı

        **İşlem Verileri:**
        - Portföy bilgileri
        - Hisse senedi işlem geçmişi
        - Watchlist ve alert ayarları

        **Teknik Veriler:**
        - Oturum bilgileri
        - Erişim logları (son 90 gün)
        """)

        # Data retention info
        st.markdown("### 📅 Veri Saklama Süreleri")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Aktif Kullanıcı Verileri", "Hesap aktif olduğu sürece")
            st.metric("İşlem Geçmişi", "2 yıl")
        with col2:
            st.metric("Pasif Hesap Anonimleştirme", "2 yıl inaktivite sonrası")
            st.metric("Log Kayıtları", "90 gün")

    with tab3:
        st.subheader("📥 Veri Taşınabilirliği (KVKK/GDPR Hakkı)")

        st.markdown("""
        KVKK ve GDPR kapsamında, tüm kişisel verilerinizi makine tarafından okunabilir
        bir formatta (JSON) talep etme hakkınız vardır.

        **Veri paketi şunları içerir:**
        - Kullanıcı profili
        - Portföyler ve holdingleriniz
        - İşlem geçmişi
        - Watchlist'ler
        - Alert ayarları
        - İzin kayıtları
        """)

        if st.button("📥 Verilerimi İndir (JSON)", type="primary"):
            with st.spinner("Verileriniz hazırlanıyor..."):
                data = gdpr.export_user_data(user_id)

                # Convert to JSON
                json_data = json.dumps(data, indent=2, ensure_ascii=False, default=str)

                st.download_button(
                    label="💾 JSON Dosyasını İndir",
                    data=json_data,
                    file_name=f"fundportal_data_{user_id}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

                st.success("✅ Verileriniz hazır! İndirme butonuna tıklayın.")

    with tab4:
        st.subheader("🗑️ Hesabı Silme (Unutulma Hakkı)")

        st.warning("""
        ⚠️ **DİKKAT:** Bu işlem geri alınamaz!

        Hesabınızı sildiğinizde:
        - Tüm portföy ve işlem verileriniz kalıcı olarak silinir
        - Watchlist ve alert'leriniz kaldırılır
        - Kullanıcı bilgileriniz anonimleştirilir
        - 30 gün içinde bu işlemi iptal edebilirsiniz
        """)

        # Check if there's a pending deletion request
        conn = gdpr.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM deletion_requests
            WHERE user_id = ? AND status = 'pending'
            ORDER BY id DESC LIMIT 1
        """, (user_id,))
        pending_deletion = cursor.fetchone()
        conn.close()

        if pending_deletion:
            st.error(f"""
            ⏳ Aktif silme talebiniz var!

            **Talep Tarihi:** {pending_deletion['request_date']}
            **Planlanan Silme:** {pending_deletion['scheduled_deletion_date']}

            30 gün içinde fikrini değiştirebilirsiniz.
            """)

            if st.button("↩️ Silme Talebini İptal Et"):
                if gdpr.cancel_deletion_request(pending_deletion['id']):
                    st.success("✅ Silme talebiniz iptal edildi!")
                    st.rerun()
        else:
            st.markdown("### Hesap Silme Talebi")

            agree_1 = st.checkbox("Tüm verilerimin kalıcı olarak silineceğini anlıyorum")
            agree_2 = st.checkbox("Bu işlemin geri alınamayacağını kabul ediyorum")

            if agree_1 and agree_2:
                if st.button("🗑️ HESABIMI SİL", type="primary"):
                    request_id = gdpr.request_data_deletion(user_id, grace_period_days=30)
                    st.success(f"""
                    ✅ Silme talebiniz alındı!

                    Hesabınız 30 gün içinde silinecek.
                    Bu süre içinde fikrinizi değiştirirseniz, talebi iptal edebilirsiniz.
                    """)
                    st.rerun()

    with tab5:
        st.subheader("📜 Veri İşleme Audit Trail")

        st.markdown("Son 90 günlük veri erişim logları:")

        access_logs = gdpr.get_data_access_audit_trail(user_id, days=90)

        if access_logs:
            # Display as table
            import pandas as pd
            df = pd.DataFrame(access_logs)

            # Select relevant columns
            if not df.empty:
                display_df = df[['timestamp', 'access_type', 'data_type', 'purpose']].copy()
                display_df.columns = ['Tarih', 'İşlem Tipi', 'Veri Tipi', 'Amaç']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Henüz erişim logu bulunmuyor.")

        # Consent audit trail
        st.markdown("### İzin Değişiklikleri")
        consent_logs = gdpr.get_consent_audit_trail(user_id)

        if consent_logs:
            for log in consent_logs[:10]:
                status_icon = "✅" if log['is_granted'] else "❌"
                date = log.get('granted_at') or log.get('withdrawn_at', 'N/A')
                st.text(f"{status_icon} {log['consent_type']} - {date}")


def check_user_consents(user_id: int) -> bool:
    """Check if user has granted required consents

    Args:
        user_id: User ID

    Returns:
        True if all required consents are granted
    """
    gdpr = GDPRComplianceManager()
    consents = gdpr.get_user_consents(user_id)

    # Required consents
    has_privacy = consents.get('privacy_policy', False)
    has_terms = consents.get('terms_of_service', False)

    return has_privacy and has_terms


def init_consent_versions():
    """Initialize default consent document versions"""
    gdpr = GDPRComplianceManager()

    # Check if versions exist
    privacy_version = gdpr.get_active_consent_version('privacy_policy')
    if not privacy_version:
        gdpr.add_consent_version(
            'privacy_policy',
            '1.0',
            get_privacy_policy('tr'),
            datetime.now()
        )

    terms_version = gdpr.get_active_consent_version('terms_of_service')
    if not terms_version:
        gdpr.add_consent_version(
            'terms_of_service',
            '1.0',
            get_terms_of_service(),
            datetime.now()
        )
