/*
 * SuicaDBTest.kt
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package au.id.micolous.metrodroid.test

import au.id.micolous.metrodroid.transit.suica.SuicaDBUtil
import au.id.micolous.metrodroid.util.Preferences
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

/**
 * Tests for the Suica station and bus stop databases built from data/suica.
 */
class SuicaDBTest : BaseInstrumentedTest() {
    private fun english() {
        setLocale("en-US")
        Preferences.showRawStationIds = false
        Preferences.showBothLocalAndEnglish = false
    }

    @Test
    fun testBusStopsUseFullCodes() {
        english()
        // These two stops share the same low bytes (line 0x15, stop 0xf5), and used to collide.
        val a = assertNotNull(SuicaDBUtil.getBusStop(0, 0x15, 0x55f5))
        assertEquals("Kencho Station Kamiyacho", a.getStationName(false).unformatted)
        val b = assertNotNull(SuicaDBUtil.getBusStop(0, 0xf15, 0x55f5))
        assertEquals("Kamiyachō kenchō mae", b.getStationName(false).unformatted)
    }

    @Test
    fun testNewBusStop() {
        english()
        // Kyoto Bus, Kiyomizu-michi (issue #863). Only has a Japanese name.
        val s = assertNotNull(SuicaDBUtil.getBusStop(0, 0xe09, 0x119))
        assertEquals("清水道", s.getStationName(false).unformatted)
        assertEquals("京都バス", s.companyName?.unformatted)
    }

    @Test
    fun testBusOperatorFallback() {
        english()
        // Unknown stop for a known operator falls back to the operator's common entry.
        val s = assertNotNull(SuicaDBUtil.getBusStop(0, 0xc69, 0x1234))
        assertEquals("Keihin Express Bus", s.companyName?.unformatted)
        assertNull(SuicaDBUtil.getBusStop(0, 0, 0))
    }

    @Test
    fun testRenamedRailStation() {
        english()
        // JR East Tōkaidō line 0x01 station 0x06 is now Takanawa Gateway (opened 2020). The
        // legacy English name (Tamachi) must not be reused for it.
        val s = assertNotNull(SuicaDBUtil.getRailStation(0, 0x01, 0x06))
        assertEquals("高輪ゲートウェイ", s.getStationName(false).unformatted)
        assertEquals("JR East", s.companyName?.unformatted)

        // Tamachi itself keeps its English name.
        val tamachi = assertNotNull(SuicaDBUtil.getRailStation(0, 0x01, 0x05))
        assertEquals("Tamachi", tamachi.getStationName(false).unformatted)
    }
}
